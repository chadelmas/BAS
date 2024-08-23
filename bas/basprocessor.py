# Copyright (C) 2023-2024 CS GROUP France, https://csgroup.eu
#
# This file is part of BAS (Buffer Around Sections)
#
#     https://github.com/CS-SI/BAS
#
# Authors:
#     Charlotte Emery
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
basprocessor.py
: From an external watermask + a (set of) river centerline(s) and associated node along it (stations or calculus points),
derive a width estimation at said-nodes observed within the mask
"""
import os
from datetime import datetime
import geopandas as gpd
import pandas as pd
from pyproj import CRS
import rasterio as rio
import shapely
from shapely.geometry import MultiLineString, LineString, MultiPolygon
import numpy as np

from tools import DisjointBboxError, FileExtensionError
from watermask import WaterMask
from widths import compute_widths_from_single_watermask
from sections_reduction import reduce_section
from constants import FLT_TOL_LEN_DEFAULT, FLT_TOL_DIST_DEFAULT


# os.environ['USE_PYGEOS'] = '0'


class BASProcessor:

    def __init__(self,
                 str_watermask_tif=None,
                 gdf_sections=None,
                 gdf_reaches=None,
                 attr_reachid=None,
                 str_proj="proj",
                 str_provider=None,
                 str_datetime=None):
        """Class constructor
        """

        # Set watermask information
        if str_watermask_tif is not None:
            self.f_watermask_in = str_watermask_tif
            if not os.path.isfile(str_watermask_tif):
                raise FileExistsError("Input watermask GeoTiff does not exist")
        else:
            raise ValueError("Missing watermask GeoTiff input file")
        self.scene_name = os.path.basename(self.f_watermask_in).split(".")[0]
        self.proj = str_proj
        self.provider = str_provider
        self.watermask = None

        # Set sections information
        if gdf_sections is None:
            raise ValueError("Missing reaches geometries")
        else:
            if not isinstance(gdf_sections, gpd.GeoDataFrame):
                raise TypeError
        self.gdf_sections = gdf_sections

        # Set reaches information
        if gdf_reaches is None:
            raise ValueError("Missing reaches geometries")
        else:
            if not isinstance(gdf_reaches, gpd.GeoDataFrame):
                raise TypeError
        self.gdf_reaches = gdf_reaches
        self.attr_reachid = attr_reachid

        # Set datetime information if provided
        if str_datetime is not None:
            self.scene_datetime = str_datetime
            try:
                dt_scene = datetime.strptime(self.scene_datetime, "%Y%m%dT%H%M%S")
            except ValueError:
                raise ValueError("input datetime {} does not match format '%Y%m%dT%H%M%S'.".format(self.scene_datetime))
        else:
            self.scene_datetime = None

        # Processing default values
        self.dct_cfg = {"clean": {"bool_toclean": True,
                                  "type_clean": "base",
                                  "fpath_wrkdir": ".",
                                  "gdf_waterbodies": None
                                  },
                        "label": {"bool_tolabel": False,
                                  "type_label": "base",
                                  "fpath_wrkdir": "."
                                  },
                        "reduce": {
                            "how": "simple",
                            "attr_locxs": "loc_xs",
                            "attr_nb_chan_max": "n_chan_max",
                            "attr_nodepx": "proj_x",
                            "attr_nodepy": "proj_y"
                        },
                        "widths": {"scenario": 0
                                   }
                        }

    def check_bbox_compatibility(self):
        """Check if sections and watermask are spatially compatible
        """

        print("----- WidthProcessing = CheckBboxCompatibility -----")
        print("")

        if self.gdf_sections.crs != CRS(4326):
            gdf_crs_sections = self.gdf_sections.to_crs(CRS(4326))
        else:
            gdf_crs_sections = self.gdf_sections.copy(deep=True)
        bbox_sections = gdf_crs_sections.total_bounds
        polygon_sections = shapely.geometry.box(*bbox_sections)  # Convert bbox to Polygon object
        # Shapely 2.0 : box(xmin, ymin, xmax, ymax, ccw=True, **kwargs)

        bbox_watermask = self.watermask.get_bbox()  # Load watermask bbox in lonlat
        polygon_watermask = shapely.geometry.box(*bbox_watermask)  # Convert watermask bbox to Polygon object

        if polygon_watermask.disjoint(polygon_sections):
            raise DisjointBboxError

        print("")
        print("----- CheckBboxCompatibility : Done -----")

    def preprocessing(self):
        """Preprocessing: load watermask, reproject sections et check bounding boxes intersections
        """

        print("----- WidthProcessing = Preprocessing -----")
        print("")

        # Load WaterMask object
        self.watermask = WaterMask.from_tif(self.f_watermask_in, self.provider, self.proj)

        # Reproject sections to watermask coordinate system
        self.gdf_reaches = self.gdf_reaches.to_crs(self.watermask.crs_epsg)
        self.gdf_sections = self.gdf_sections.to_crs(self.watermask.crs_epsg)

        # Check boundingbox compatibility
        self.check_bbox_compatibility()

        print("")
        print("----- Preprocessing : Done -----")

    def read_cfg(self, dct_cfg=None):
        """ Add default value to dct_cfg if keywords are missing

        Parameters
        ----------
        dct_cfg : dict

        Returns
        -------
        dct_cfg : dict

        """

        for key in ["clean", "label", "widths"]:
            if key not in dct_cfg.keys():
                dct_cfg[key] = self.dct_cfg[key]

            else:
                for subkey in self.dct_cfg[key].keys():
                    if subkey not in self.dct_cfg[key].keys():
                        dct_cfg[key][subkey] = self.dct_cfg[key][subkey]
        return dct_cfg

    def processing(self, dct_cfg=None, str_fpath_dir_out="."):
        """Processing : extraction of widths from watermask

        Parameters
        ----------
        dct_cfg : set processing configuration
        { "clean" : { "bool_clean" : True/False,
                      "type_clean" : base/waterbodies,
                      "fpath_wrkdir" : "."
                      "gdf_waterbodies" : gdf with polygon waterbodies to clean waterbodies [optionnal]
                    },
          "label" : { "bool_label" : True/False,
                      "type_label" : base,
                      "fpath_wrkdir" : "."
                    },
          "widths" : { scenario : 0/1/10/11
                     }
        }

        Returns
        -------
        gdf_widths : gpd.GeoDataFrame

        """

        print("----- WidthProcessing = Processing -----")
        print("")

        # Check cfg
        dct_cfg = self.read_cfg(dct_cfg)

        # Clean watermask
        if dct_cfg["clean"]["bool_clean"]:
            self.clean_watermask(dct_cfg)

        # Label watermask
        if dct_cfg["label"]["bool_label"]:
            self.label_watermask()

        print("")
        print("----- Processing : Done -----")

    def clean_watermask(self, dct_cfg=None):
        """Clean watermask from non-river waterbodies

        Parameters
        ----------
        Returns
        -------

        """

        print(" ---- Cleaning watermask ---- ")

        # Check config_dct
        if dct_cfg is None:
            dct_cfg = self.dct_cfg

        # Gather reaches and project them into the watermask coordinate system
        gdf_reaches_proj = self.gdf_reaches.to_crs(epsg=self.watermask.crs_epsg)

        # Gather wm as polygons
        gdf_wm_polygons = self.watermask.get_polygons(bool_clean=False,
                                                      bool_label=False,
                                                      bool_exterior_only=False,
                                                      bool_indices=True)

        # Apply regular cleaning
        gdf_join_wm_reaches = gpd.sjoin(left_df=gdf_wm_polygons,
                                        right_df=gdf_reaches_proj,
                                        how="inner",
                                        predicate="intersects")
        npar_idx_pol_notclean = np.setdiff1d(
            np.unique(gdf_wm_polygons.index),
            np.unique(gdf_join_wm_reaches.index)
        )

        # Apply waterbodies-type cleaning if activated
        if dct_cfg["clean"]["gdf_waterbodies"] is not None and dct_cfg["clean"]["type_clean"] == "waterbodies":

            if not isinstance(dct_cfg["clean"]["gdf_waterbodies"], gpd.GeoDataFrame):
                raise TypeError
            else:
                gdf_waterbodies_wrk = dct_cfg["clean"]["gdf_waterbodies"].to_crs(gdf_wm_polygons.crs)

            gdf_join_wm_waterbodies = gpd.sjoin(left_df=gdf_wm_polygons,
                                                right_df=gdf_waterbodies_wrk,
                                                how="inner",
                                                predicate="intersects")

            npar_idx_notclean_wb = np.setdiff1d(
                np.unique(gdf_wm_polygons.index),
                np.unique(gdf_join_wm_waterbodies.index)
            )

            npar_idx_pol_notclean = np.intersect1d(npar_idx_pol_notclean, npar_idx_notclean_wb)

        # Get pixc indexes from polygon indexes
        gdfsub_notclean_wm_polygons = gdf_wm_polygons.loc[npar_idx_pol_notclean, :].copy()
        l_idx_pixc_notclean = [
            element for list_ in gdfsub_notclean_wm_polygons["indices"].values for element in list_
        ]

        # Update clean flag in the watermask
        self.watermask.update_clean_flag(mask=l_idx_pixc_notclean)

    def label_watermask(self):
        """Label watermask into individual regions associated to a unique reach each
        """

        print(" ---- Label watermask ---- ")

        # Gather reaches and project them into the watermask coordinate system
        gdf_reaches_proj = self.gdf_reaches.loc[:, [self.attr_reachid, "geometry"]].to_crs(epsg=self.watermask.crs_epsg)

        # Associate each pixel from wm to the closest reach
        gdf_label = gpd.sjoin_nearest(left_df=self.watermask.gdf_wm_as_pixc,
                                      right_df=gdf_reaches_proj,
                                      max_distance=3000.,
                                      how="inner",
                                      distance_col="dist")
        dct_label_update = {
            key: list(group) for key, group in gdf_label.groupby(by="index_right").groups.items()
        }
        self.watermask.update_label_flag(dct_label_update)

    def _prepare_tol_inputs(self, str_input_name=None, obj_to_prepare=None, default_value=0.):
        """

        :param str_input_name: str
            key pointing towards the parameter to prepare
        :param obj_to_prepare: dict
            dict with configuration parameter
        :param default_value:
            default value of parameter, if key str_input_name is not in obj_to_prepare dictionnary
        :return:
        """

        if str_input_name is None:
            raise ValueError("Missing input argument 'str_input_name' for method '_prepare_tol_inputs'")
        if obj_to_prepare is None:
            raise ValueError("Missing input argument 'obj_to_prepare' for method '_prepare_tol_inputs'")

        try:

            if isinstance(obj_to_prepare[str_input_name], float):  # Unique value
                self.gdf_sections.insert(loc=2, column=str_input_name, value=obj_to_prepare[str_input_name])

            # To debug
            elif isinstance(obj_to_prepare[str_input_name], str):  # Column name in self.gdf_sections (from inputs)

                self.gdf_sections.rename(columns={obj_to_prepare[str_input_name]: str_input_name}, inplace=True)

            else:
                raise TypeError("Unexpected type of config input', "
                                "got {}, expecting (int, str)".format(obj_to_prepare[str_input_name].__class__))

        except KeyError:  # entry is not defined
            self.gdf_sections.insert(loc=2, column=str_input_name, value=default_value)

    def _reduce_sections_over_reach(self, reach_id=None,
                                    lin_reach=None,
                                    pol_region=None,
                                    dct_cfg=None):
        """Reduce all sections over a single reach

        :param reach_id: (str,int)
            ID of current reach
        :param lin_reach: LineString
            geometry of the centerline/reach
        :param pol_region: (Polygon/MultiPolygon)
            geometry of the vectorized watermask associated to the current reach
        :param dct_cfg: dict
            configuration dictionnary
        :return: GeoDataFrame
            gdfsub_sections_byreach_onregion
        """

        gdfsub_sections_byreach = self.gdf_sections[self.gdf_sections[self.attr_reachid] == reach_id].copy(
            deep=True)

        # In sections subset, keep only sections that intersect current region
        ser_bool_intersects = gdfsub_sections_byreach["geometry"].intersects(pol_region)
        gdfsub_sections_byreach_onregion = gdfsub_sections_byreach[ser_bool_intersects].copy(deep=True)

        # For remaining stations/sections, reduce their geometry to within the current region
        if len(gdfsub_sections_byreach_onregion) > 0:

            try:
                gdfsub_sections_byreach_onregion["geometry"] = gdfsub_sections_byreach_onregion.apply(
                    lambda x: reduce_section(how=dct_cfg["reduce"]["how"],
                                             lin_long_in=x.geometry,
                                             pol_in=pol_region,
                                             lin_rch_in=lin_reach,
                                             flt_section_xs_along_rch=x[dct_cfg["reduce"]["attr_locxs"]],
                                             flt_node_proj_x=x[dct_cfg["reduce"]["attr_nodepx"]],
                                             flt_node_proj_y=x[dct_cfg["reduce"]["attr_nodepy"]],
                                             int_nb_chan_max=x[dct_cfg["reduce"]["attr_nb_chan_max"]],
                                             flt_tol_len=x["flt_tol_len"],
                                             flt_tol_dist=x["flt_tol_dist"]
                                             ),
                    axis=1)

            except KeyError:

                if dct_cfg["reduce"]["how"] != "simple":
                    print("Warning: Missing inputs for reduce_type different from 'simple'.")
                gdfsub_sections_byreach_onregion["geometry"] = gdfsub_sections_byreach_onregion.apply(
                    lambda x: reduce_section(how=dct_cfg["reduce"]["how"],
                                             lin_long_in=x.geometry,
                                             pol_in=pol_region,
                                             lin_rch_in=lin_reach),
                    axis=1)

            gdfsub_sections_byreach_onregion = gdfsub_sections_byreach_onregion[
                ~gdfsub_sections_byreach_onregion["geometry"].is_empty]

            return gdfsub_sections_byreach_onregion

    def reduce_sections(self, dct_cfg=None, flt_tol_len=FLT_TOL_LEN_DEFAULT, flt_tol_dist=FLT_TOL_DIST_DEFAULT):
        """Reduce sections geometry to its associated region

        Parameters
        ----------

        Returns
        -------
        gdf_sections_out : gpd.GeoDataFrame
            reduced sections geometry

        """

        print(" ---- Reduce sections ---- ")

        # Check config_dct
        if dct_cfg is None:
            dct_cfg = self.dct_cfg

        if "reduce" not in dct_cfg.keys():
            dct_cfg["reduce"] = self.dct_cfg["reduce"]

        if dct_cfg["reduce"]["how"] != "simple":
            # Prepare input flt_tol_len
            self._prepare_tol_inputs(str_input_name="flt_tol_len",
                                     obj_to_prepare=dct_cfg["reduce"],
                                     default_value=flt_tol_len)

            # Prepare input flt_tol_dist
            self._prepare_tol_inputs(str_input_name="flt_tol_dist",
                                     obj_to_prepare=dct_cfg["reduce"],
                                     default_value=flt_tol_dist)

        gdf_wm_labelled_pol = self.watermask.get_polygons(
            bool_clean=dct_cfg["clean"]["bool_clean"],
            bool_label=dct_cfg["label"]["bool_label"],
            bool_indices=False,
            bool_exterior_only=False
        )

        l_gdfsub_sections = []
        for label, group in gdf_wm_labelled_pol.groupby(by="label").groups.items():
            pol_region = MultiPolygon(gdf_wm_labelled_pol.loc[group, "geometry"].tolist())

            # Extract sections associated to unique current reach
            reach_id = self.gdf_reaches.at[label, self.attr_reachid]
            lin_reach = self.gdf_reaches.at[label, "geometry"]

            gdfsub_sections_byreach_onregion = self._reduce_sections_over_reach(reach_id=reach_id,
                                                                                lin_reach=lin_reach,
                                                                                pol_region=pol_region,
                                                                                dct_cfg=dct_cfg)

            l_gdfsub_sections.append(gdfsub_sections_byreach_onregion)

        # Gather all sections
        gdf_sections_out = pd.concat(l_gdfsub_sections)

        return gdf_sections_out

    def postprocessing(self, dct_cfg=None, str_fpath_dir_out=".", str_fpath_wm_in=None):
        """

        :param str_fpath_wm_in:
        :param dct_cfg:
        :param str_fpath_dir_out:
        :return:
        """

        print("----- WidthProcessing = PostProcessing -----")
        print("")

        # Prepare sections
        gdf_wrk_sections = self.reduce_sections(dct_cfg)

        # Process width
        print("---- Compute widths ----")
        if str_fpath_wm_in is None:
            str_fpath_wm_tif = self.watermask.save_wm(fmt="tif",
                                                  bool_clean=dct_cfg["clean"]["bool_clean"],
                                                  bool_label=dct_cfg["label"]["bool_label"],
                                                  str_fpath_dir_out=str_fpath_dir_out,
                                                  str_suffix="readytouse")
        else:
            str_fpath_wm_tif = str_fpath_wm_in

        with rio.open(str_fpath_wm_tif) as src:
            gdf_widths, _ = compute_widths_from_single_watermask(scenario=dct_cfg["widths"]["scenario"],
                                                                 watermask=src,
                                                                 sections=gdf_wrk_sections,
                                                                 buffer_length=8.0 * self.watermask.res)

        print("")
        print("----- PostProcessing : Done -----")

        return gdf_widths, str_fpath_wm_tif
