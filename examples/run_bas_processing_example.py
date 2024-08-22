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

import sys

sys.path.append("/home/cemery/Work/git/BAS/bas")

import geopandas as gpd

from basprocessor import BASProcessor
from rivergeomproduct import RiverGeomProduct

# Input file
watermask_tif = "example_watermask.tif"
ref_watermask_tif = "example_ref_waterbodies.shp"

# Simple example : sections are ready to use
shp_reaches_smpl = "example_reaches_simple.shp"
shp_sections_smpl = "example_sections_simple.shp"

# Complex example : sections have to be derived
shp_reaches_cplx = "example_reaches_cplx.shp"
shp_nodes_cplx = "example_nodes_cplx_up.shp"


def example_1():
    """Example_1 :
        No watermask cleaning and no watermask labelling
        Sections available
        Width only
    """

    print("===== BASProcessing Example #1 = BEGIN =====")
    print("")

    # Set config #1
    dct_cfg_V1 = {"clean": {"bool_clean": False,
                            "type_clean": "base",
                            "fpath_wrkdir": ".",
                            "gdf_waterbodies": None
                            },
                  "label": {"bool_label": False,
                            "type_label": "base",
                            "fpath_wrkdir": "."
                            },
                  "reduce": {"how": "simple",
                             "attr_nb_chan_max": None},
                  "widths": {"scenario": 0
                             }
                  }

    # Instanciate basprocessor
    processor = BASProcessor(
        str_watermask_tif=watermask_tif,
        gdf_sections=gdf_sections,
        gdf_reaches=gdf_reaches,
        attr_reachid="id",
        str_proj="proj",
        str_provider="EO"
    )
    processor.preprocessing()
    processor.processing(dct_cfg_V1)
    gdf_widths, _ = processor.postprocessing(dct_cfg_V1)
    print(gdf_widths)
    gdf_widths.to_file("widths_example1.shp")

    print("")
    print("===== BASProcessing Example #1 = END =====")


def example_2():
    """Example_2 :
        Basic watermask cleaning without reference waterbodies and no watermask labelling
        Sections available
        Width + estimation of intersection width other sections
    """

    print("===== BASProcessing Example #2 = BEGIN =====")
    print("")

    # Set config #2
    dct_cfg_V2 = {"clean": {"bool_clean": True,
                            "type_clean": "base",
                            "fpath_wrkdir": ".",
                            "gdf_waterbodies": None
                            },
                  "label": {"bool_label": False,
                            "type_label": "base",
                            "fpath_wrkdir": "."
                            },
                  "widths": {"scenario": 11
                             }
                  }

    # Instanciate basprocessor
    processor = BASProcessor(
        str_watermask_tif=watermask_tif,
        gdf_sections=gdf_sections,
        gdf_reaches=gdf_reaches,
        attr_reachid="id",
        str_proj="proj",
        str_provider="EO"
    )
    processor.preprocessing()
    processor.processing(dct_cfg_V2)
    gdf_widths, _ = processor.postprocessing(dct_cfg_V2)
    print(gdf_widths)
    gdf_widths.to_file("widths_example2.shp")

    print("")
    print("===== BASProcessing Example #2 = END =====")


def example_3():
    """Example_3 :
        Watermask cleaning with reference waterbodies and no watermask labelling
        Sections available
        Width only
    """

    print("===== BASProcessing Example #3 = BEGIN =====")
    print("")

    # Set config #3
    dct_cfg_V3 = {"clean": {"bool_clean": True,
                            "type_clean": "waterbodies",
                            "fpath_wrkdir": ".",
                            "gdf_waterbodies": gdf_waterbodies
                            },
                  "label": {"bool_label": False,
                            "type_label": "base",
                            "fpath_wrkdir": "."
                            },
                  "widths": {"scenario": 0
                             }
                  }

    # Instanciate basprocessor
    processor = BASProcessor(
        str_watermask_tif=watermask_tif,
        gdf_sections=gdf_sections,
        gdf_reaches=gdf_reaches,
        attr_reachid="id",
        str_proj="proj",
        str_provider="EO"
    )
    processor.preprocessing()
    processor.processing(dct_cfg_V3)
    gdf_widths, _ = processor.postprocessing(dct_cfg_V3)
    print(gdf_widths)
    gdf_widths.to_file("widths_example3.shp")

    print("")
    print("===== BASProcessing Example #3 = END =====")


def example_4():
    """Example_4 :
        Watermask cleaning with reference waterbodies + watermask labelling
        Sections available
        Width only
    """

    print("===== BASProcessing Example #4 = BEGIN =====")
    print("")

    # Set config #4
    dct_cfg_V4 = {"clean": {"bool_clean": True,
                            "type_clean": "waterbodies",
                            "fpath_wrkdir": ".",
                            "gdf_waterbodies": gdf_waterbodies
                            },
                  "label": {"bool_label": True,
                            "type_label": "base",
                            "fpath_wrkdir": "."
                            },
                  "widths": {"scenario": 0
                             }
                  }

    # Instanciate basprocessor
    processor = BASProcessor(
        str_watermask_tif=watermask_tif,
        gdf_sections=gdf_sections,
        gdf_reaches=gdf_reaches,
        attr_reachid="id",
        str_proj="proj",
        str_provider="EO"
    )
    processor.preprocessing()
    processor.processing(dct_cfg_V4)
    gdf_widths, _ = processor.postprocessing(dct_cfg_V4)
    print(gdf_widths)
    gdf_widths.to_file("widths_example4.shp")

    print("")
    print("===== BASProcessing Example #4 = END =====")


def example_5():
    """Example_5 :
        Watermask cleaning with reference waterbodies + watermask labelling
        Sections NOT available
        Reduce section - "hydrogeom" + providing tolerance values as constant
    """

    print("===== BASProcessing Example #5 = BEGIN =====")
    print("")

    # Load reaches
    gdf_reaches_cplx = gpd.read_file(shp_reaches_cplx)
    gdf_nodes_cplx = gpd.read_file(shp_nodes_cplx)

    # Compute sections
    dct_geom_attr = {"reaches": {"reaches_id": "reach_id"},
                     "nodes": {"reaches_id": "reach_id",
                               "nodes_id": "node_id",
                               "pwidth": "p_width",
                               "pwse": "p_wse"}}
    obj_rivergeom = RiverGeomProduct.from_shp(reaches_shp=shp_reaches_cplx,
                                              nodes_shp=shp_nodes_cplx,
                                              bool_edge=False,
                                              dct_attr=dct_geom_attr)
    obj_rivergeom.draw_allreaches_centerline()
    gdf_sections_ortho = obj_rivergeom.draw_allreaches_sections(type="ortho", flt_factor_width=15.)

    # Set configs #5
    dct_cfg_V5 = {"clean": {"bool_clean": True,
                            "type_clean": "waterbodies",
                            "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples",
                            "gdf_waterbodies": gdf_waterbodies
                            },
                  "label": {"bool_label": True,
                            "type_label": "base",
                            "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples"
                            },
                  "reduce": {"how": "hydrogeom",
                             "attr_nb_chan_max": "n_chan_max",
                             "attr_locxs": "loc_xs",
                             "attr_nodepx": "x_proj",
                             "attr_nodepy": "y_proj",
                             "flt_tol_len": 0.05,
                             "flt_tol_dist": 1000.},
                  "widths": {"scenario": 11
                             }
                  }

    gdf_sections_ortho.insert(loc=2, column=dct_cfg_V5["reduce"]["attr_nb_chan_max"], value=0)
    gdf_sections_ortho[dct_cfg_V5["reduce"]["attr_nb_chan_max"]] = gdf_nodes_cplx.loc[
        gdf_sections_ortho.index, dct_cfg_V5["reduce"]["attr_nb_chan_max"]]

    # Instanciate basprocessor(s)
    processor_a = BASProcessor(
        str_watermask_tif=watermask_tif,
        gdf_sections=gdf_sections_ortho,
        gdf_reaches=gdf_reaches_cplx,
        attr_reachid="reach_id",
        str_proj="proj",
        str_provider="EO"
    )
    processor_a.preprocessing()

    gser_proj_nodes = gdf_nodes_cplx["geometry"].to_crs(processor_a.watermask.crs)

    processor_a.gdf_sections.insert(loc=3, column=dct_cfg_V5["reduce"]["attr_nodepx"], value=0.)
    processor_a.gdf_sections[dct_cfg_V5["reduce"]["attr_nodepx"]] = gser_proj_nodes.loc[
        processor_a.gdf_sections.index].x

    processor_a.gdf_sections.insert(loc=4, column=dct_cfg_V5["reduce"]["attr_nodepy"], value=0.)
    processor_a.gdf_sections[dct_cfg_V5["reduce"]["attr_nodepy"]] = gser_proj_nodes.loc[
        processor_a.gdf_sections.index].y

    processor_a.processing(dct_cfg_V5)

    gdf_widths_a, _ = processor_a.postprocessing(dct_cfg_V5)

    gdf_widths_a["reach_id"] = gdf_widths_a["reach_id"].astype(str)
    gdf_widths_a["node_id"] = gdf_widths_a["node_id"].astype(int).astype(str)
    gdf_widths_a.to_file("widths_example5.shp")

    print("")
    print("===== BASProcessing Example #5 = END =====")


def example_6():
    """Example_6 :
        Watermask cleaning with reference waterbodies + watermask labelling
        Sections NOT available
        Reduce section - "hydrogeom" + WITHOUT providing tolerance values
    """

    print("===== BASProcessing Example #6 = BEGIN =====")
    print("")

    # Load reaches
    gdf_reaches_cplx = gpd.read_file(shp_reaches_cplx)
    gdf_nodes_cplx = gpd.read_file(shp_nodes_cplx)

    # Compute sections
    dct_geom_attr = {"reaches": {"reaches_id": "reach_id"},
                     "nodes": {"reaches_id": "reach_id",
                               "nodes_id": "node_id",
                               "pwidth": "p_width",
                               "pwse": "p_wse"}}
    obj_rivergeom = RiverGeomProduct.from_shp(reaches_shp=shp_reaches_cplx,
                                              nodes_shp=shp_nodes_cplx,
                                              bool_edge=False,
                                              dct_attr=dct_geom_attr)
    obj_rivergeom.draw_allreaches_centerline()
    gdf_sections_ortho = obj_rivergeom.draw_allreaches_sections(type="ortho", flt_factor_width=15.)

    # Set configs #5
    dct_cfg_V6 = {"clean": {"bool_clean": True,
                            "type_clean": "waterbodies",
                            "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples",
                            "gdf_waterbodies": gdf_waterbodies
                            },
                  "label": {"bool_label": True,
                            "type_label": "base",
                            "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples"
                            },
                  "reduce": {"how": "hydrogeom",
                             "attr_nb_chan_max": "n_chan_max",
                             "attr_locxs": "loc_xs",
                             "attr_nodepx": "x_proj",
                             "attr_nodepy": "y_proj"},
                  "widths": {"scenario": 11
                             }
                  }

    gdf_sections_ortho.insert(loc=2, column=dct_cfg_V6["reduce"]["attr_nb_chan_max"], value=0)
    gdf_sections_ortho[dct_cfg_V6["reduce"]["attr_nb_chan_max"]] = gdf_nodes_cplx.loc[
        gdf_sections_ortho.index, dct_cfg_V6["reduce"]["attr_nb_chan_max"]]

    # Instanciate basprocessor(s)
    processor_a = BASProcessor(
        str_watermask_tif=watermask_tif,
        gdf_sections=gdf_sections_ortho,
        gdf_reaches=gdf_reaches_cplx,
        attr_reachid="reach_id",
        str_proj="proj",
        str_provider="EO"
    )
    processor_a.preprocessing()

    gser_proj_nodes = gdf_nodes_cplx["geometry"].to_crs(processor_a.watermask.crs)

    processor_a.gdf_sections.insert(loc=3, column=dct_cfg_V6["reduce"]["attr_nodepx"], value=0.)
    processor_a.gdf_sections[dct_cfg_V6["reduce"]["attr_nodepx"]] = gser_proj_nodes.loc[
        processor_a.gdf_sections.index].x

    processor_a.gdf_sections.insert(loc=4, column=dct_cfg_V6["reduce"]["attr_nodepy"], value=0.)
    processor_a.gdf_sections[dct_cfg_V6["reduce"]["attr_nodepy"]] = gser_proj_nodes.loc[
        processor_a.gdf_sections.index].y

    processor_a.processing(dct_cfg_V6)

    gdf_widths_a, _ = processor_a.postprocessing(dct_cfg_V6)

    gdf_widths_a["reach_id"] = gdf_widths_a["reach_id"].astype(str)
    gdf_widths_a["node_id"] = gdf_widths_a["node_id"].astype(int).astype(str)
    gdf_widths_a.to_file("widths_example6.shp")

    print("")
    print("===== BASProcessing Example #6 = END =====")


def example_7():
    """Example_7 :
        Watermask cleaning with reference waterbodies + watermask labelling
        Sections NOT available
        2 width products over the same mask
    """

    print("===== BASProcessing Example #7 = BEGIN =====")
    print("")

    # Load reaches
    gdf_reaches_cplx = gpd.read_file(shp_reaches_cplx)

    # Compute sections
    dct_geom_attr = {"reaches": {"reaches_id": "reach_id"},
                     "nodes": {"reaches_id": "reach_id",
                               "nodes_id": "node_id",
                               "pwidth": "p_width",
                               "pwse": "p_wse"}}
    obj_rivergeom = RiverGeomProduct.from_shp(reaches_shp=shp_reaches_cplx,
                                              nodes_shp=shp_nodes_cplx,
                                              bool_edge=False,
                                              dct_attr=dct_geom_attr)
    obj_rivergeom.draw_allreaches_centerline()

    gdf_sections_ortho = obj_rivergeom.draw_allreaches_sections(type="ortho", flt_factor_width=15.)
    gdf_sections_ortho.to_file("/home/cemery/Work/git/BAS/examples/ex6_sections_ortho.shp")

    gdf_sections_chck = obj_rivergeom.draw_allreaches_sections(type="chck")
    gdf_sections_chck.to_file("/home/cemery/Work/git/BAS/examples/ex6_sections_chck.shp")

    # Set configs #6
    dct_cfg_V7a = {"clean": {"bool_clean": True,
                             "type_clean": "waterbodies",
                             "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples",
                             "gdf_waterbodies": gdf_waterbodies
                             },
                   "label": {"bool_label": True,
                             "type_label": "base",
                             "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples"
                             },
                   "widths": {"scenario": 11
                              }
                   }

    dct_cfg_V7b = {"clean": {"bool_clean": False,
                             "type_clean": "waterbodies",
                             "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples",
                             "gdf_waterbodies": gdf_waterbodies
                             },
                   "label": {"bool_label": False,
                             "type_label": "base",
                             "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples"
                             },
                   "widths": {"scenario": 0
                              }
                   }

    # Instanciate basprocessor(s)
    processor_a = BASProcessor(
        str_watermask_tif=watermask_tif,
        gdf_sections=gdf_sections_ortho,
        gdf_reaches=gdf_reaches_cplx,
        attr_reachid="reach_id",
        str_proj="proj",
        str_provider="EO"
    )
    processor_a.preprocessing()

    processor_a.processing(dct_cfg_V7a)

    gdf_widths_a, str_fpath_updated_wm_tif = processor_a.postprocessing(dct_cfg_V7a)
    gdf_widths_a["reach_id"] = gdf_widths_a["reach_id"].astype(str)
    gdf_widths_a["node_id"] = gdf_widths_a["node_id"].astype(int).astype(str)
    gdf_widths_a.to_file("widths_a_example7.shp")

    processor_b = BASProcessor(
        str_watermask_tif=str_fpath_updated_wm_tif,
        gdf_sections=gdf_sections_chck,
        gdf_reaches=gdf_reaches_cplx,
        attr_reachid="reach_id",
        str_proj="proj",
        str_provider="EO"
    )

    processor_b.preprocessing()

    processor_b.processing(dct_cfg_V7b)

    dct_cfg_V7b["clean"]["bool_clean"] = True
    dct_cfg_V7b["label"]["bool_label"] = True
    gdf_widths_b, _ = processor_b.postprocessing(dct_cfg_V7b)

    gdf_widths_b["reach_id"] = gdf_widths_b["reach_id"].astype(str)
    gdf_widths_b["node_id"] = gdf_widths_b["node_id"].astype(int).astype(str)
    gdf_widths_b.to_file("widths_b_example7.shp")

    print("")
    print("===== BASProcessing Example #7 = END =====")


def example_8():
    """Example_8 :
        Watermask cleaning base + watermask labelling
        Sections NOT available
        Reduce section - "hydrogeom" + providing tolerance values as series
    """

    print("===== BASProcessing Example #8 = BEGIN =====")
    print("")

    # Load reaches
    gdf_reaches_cplx = gpd.read_file(shp_reaches_cplx)
    gdf_nodes_cplx = gpd.read_file(shp_nodes_cplx)

    # Compute sections
    dct_geom_attr = {"reaches": {"reaches_id": "reach_id"},
                     "nodes": {"reaches_id": "reach_id",
                               "nodes_id": "node_id",
                               "pwidth": "p_width",
                               "pwse": "p_wse"}}
    obj_rivergeom = RiverGeomProduct.from_shp(reaches_shp=shp_reaches_cplx,
                                              nodes_shp=shp_nodes_cplx,
                                              bool_edge=False,
                                              dct_attr=dct_geom_attr)
    obj_rivergeom.draw_allreaches_centerline()
    gdf_sections_ortho = obj_rivergeom.draw_allreaches_sections(type="ortho", flt_factor_width=15.)

    # Set configs #5
    dct_cfg_V8 = {"clean": {"bool_clean": True,
                            "type_clean": "waterbodies",
                            "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples",
                            "gdf_waterbodies": gdf_waterbodies
                            },
                  "label": {"bool_label": True,
                            "type_label": "base",
                            "fpath_wrkdir": "/home/cemery/Work/git/BAS/examples"
                            },
                  "reduce": {"how": "hydrogeom",
                             "attr_nb_chan_max": "n_chan_max",
                             "attr_locxs": "loc_xs",
                             "attr_nodepx": "x_proj",
                             "attr_nodepy": "y_proj",
                             "flt_tol_len": 0.05,
                             "flt_tol_dist": "tol_dist"},
                  "widths": {"scenario": 11
                             }
                  }

    # Add specific attributes
    gdf_sections_ortho.insert(loc=2, column=dct_cfg_V8["reduce"]["attr_nb_chan_max"], value=0)
    gdf_sections_ortho[dct_cfg_V8["reduce"]["attr_nb_chan_max"]] = gdf_nodes_cplx.loc[
        gdf_sections_ortho.index, dct_cfg_V8["reduce"]["attr_nb_chan_max"]]
    gdf_sections_ortho["tol_dist"] = (0.5 * gdf_nodes_cplx.loc[gdf_sections_ortho.index, "meander_le"] /
                                      gdf_nodes_cplx.loc[gdf_sections_ortho.index, "sinuosity"])

    # Instanciate basprocessor(s)
    processor_a = BASProcessor(
        str_watermask_tif=watermask_tif,
        gdf_sections=gdf_sections_ortho,
        gdf_reaches=gdf_reaches_cplx,
        attr_reachid="reach_id",
        str_proj="proj",
        str_provider="EO"
    )
    processor_a.preprocessing()

    gser_proj_nodes = gdf_nodes_cplx["geometry"].to_crs(processor_a.watermask.crs)

    processor_a.gdf_sections.insert(loc=3, column=dct_cfg_V8["reduce"]["attr_nodepx"], value=0.)
    processor_a.gdf_sections[dct_cfg_V8["reduce"]["attr_nodepx"]] = gser_proj_nodes.loc[
        processor_a.gdf_sections.index].x

    processor_a.gdf_sections.insert(loc=4, column=dct_cfg_V8["reduce"]["attr_nodepy"], value=0.)
    processor_a.gdf_sections[dct_cfg_V8["reduce"]["attr_nodepy"]] = gser_proj_nodes.loc[
        processor_a.gdf_sections.index].y

    processor_a.processing(dct_cfg_V8)

    gdf_widths_a, _ = processor_a.postprocessing(dct_cfg_V8)

    gdf_widths_a["reach_id"] = gdf_widths_a["reach_id"].astype(str)
    gdf_widths_a["node_id"] = gdf_widths_a["node_id"].astype(int).astype(str)
    gdf_widths_a.to_file("widths_example8.shp")

    print("")
    print("===== BASProcessing Example #8 = END =====")


if __name__ == "__main__":
    # Load reference waterbodies - cfg 4-5
    gdf_waterbodies = gpd.read_file(ref_watermask_tif)

    # Load sections and reaches - cfg 1-4
    gdf_reaches = gpd.read_file(shp_reaches_smpl)
    gdf_sections = gpd.read_file(shp_sections_smpl)
    gdf_sections.rename(mapper={"segment": "id"}, inplace=True, axis=1)

    # Run example 1
    example_1()

    # Run example 2
    example_2()

    # Run example 3
    example_3()

    # Run example 4
    example_4()

    # # Run example 5
    example_5()

    # Run example 6
    example_6()

    # Run example 7
    example_7()

    # Run example 8
    example_8()
