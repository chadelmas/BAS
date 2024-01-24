"""
module widths.py
: Contains functions to compute widths from a list of cross-sections over a watermask
Created 2021
Latest modified on Jan 10, 2024
Authors: Kevin Larnier, Charlotte Emery
"""
import os
import geopandas as gpd
import numpy as np
import rasterio as rio
from rasterio.mask import mask
from rasterio.features import shapes
from shapely.geometry import Polygon, MultiPolygon

os.environ['USE_PYGEOS'] = '0'


def compute_widths_from_single_watermask(scenario, watermask, sections, buffer_length=25.0, index_attr="index",
                                         **kwargs):
    """Compute the widths for a list of cross-sections using a single watermask

        Parameters
        ----------
        scenario : int
        watermask : rasterio.DatasetReader
            Raster of the water mask (any positive value is considered as water).
        sections : geopandas.GeoDataFrame
            GeoDataFrame containing (at least) the cross-sections geometry and the length and index attributes.
        buffer_length : float
            Length of the buffer to apply to cross-sections.
        index_attr : str
            Name of the attribute that contains indexes in the GeoDataFrame.
        kwargs : dict
            Other keyword arguments:
            bool_print_dry : bool
                If true, print out information on possible dry sections
            min_width : float
                Value of the minimal width.
            fname_buffered_section : str
                Path to the output file that will contain the buffered cross-sections. Default is None (no output).
        """

    if scenario == 0:  # Estimate widths only without uncertainty estimation
        return compute_widths_from_single_watermask_base(watermask,
                                                         sections,
                                                         buffer_length=buffer_length,
                                                         index_attr=index_attr,
                                                         **kwargs)

    elif scenario == 1:  # Estimate widths + uncertainty from section intersections
        raise NotImplementedError("Scenario 1 not implemented yet..")
    elif scenario == 10:  # Estimate widths + count banks within buffer
        raise NotImplementedError("Scenario 1 not implemented yet..")
    elif scenario == 11:  # scenario 1 + scenario 10
        return compute_widths_from_single_watermask_scenario11(watermask,
                                                               sections,
                                                               buffer_length=buffer_length,
                                                               index_attr=index_attr,
                                                               **kwargs)
    else:
        raise ValueError("Undefined scenario value")


def compute_widths_from_single_watermask_base(watermask, sections, buffer_length=25.0, index_attr="index", **kwargs):
    """Compute the widths - and only width - for a list of cross-sections using a watermask

        Parameters
        ----------
        watermask : rasterio.DatasetReader
            Raster of the water mask (any positive value is considered as water).
        sections : geopandas.GeoDataFrame
            GeoDataFrame containing (at least) the cross-sections geometry and the length and index attributes.
        buffer_length : float
            Length of the buffer to apply to cross-sections.
        index_attr : str
            Name of the attribute that contains indexes in the GeoDataFrame.
        kwargs : dict
            Other keyword arguments:
            bool_print_dry : bool
                If true, print out information on possible dry sections
            min_width : float
                Value of the minimal width.
            fname_buffered_section : str
                Path to the output file that will contain the buffered cross-sections. Default is None (no output).
        """

    # Parse extra argument keywords
    bool_print_dry = False
    if "bool_print_dry" in kwargs:
        bool_print_dry = kwargs["bool_print_dry"]
    min_width = None
    if "min_width" in kwargs:
        min_width = kwargs["min_width"]
    export_buffered_sections = False
    if "export_buffered_sections" in kwargs:
        export_buffered_sections = kwargs["export_buffered_sections"]

    # Check classes of input parameters
    if not isinstance(sections, gpd.GeoDataFrame):
        raise ValueError("sections must be a geopandas GeoDataFrame")
    if not isinstance(watermask, rio.DatasetReader):
        raise ValueError("watermask must be a rasterio DatasetReader")

    if min_width is not None:
        if not isinstance(min_width, int) and not isinstance(min_width, float):
            raise ValueError("min_width must be a number")

    if not isinstance(export_buffered_sections, bool):
        raise ValueError("export_buffered_sections must be True or False")

    # Create updated_sections GeoDataFrame (result of this function)
    updated_sections = sections.copy()
    # Add a column to contain estimated width
    updated_sections.insert(len(updated_sections.columns) - 1, "width",
                            np.nan)
    # Add a column to contain flag indicating if buffer is full of water (and so potentially sections is too short)
    updated_sections.insert(len(updated_sections.columns) - 1, "flg_bufful",
                            np.nan)

    # Project sections to EPSG 3857 if necessary (to get metric distances)
    if sections.crs.to_epsg() == 4326:
        print("Inputs in epsg:4326 are projected to epsg:3857, not effective away from equator.")
        sections = sections.to_crs(epsg=3857)

    # Apply buffer to sections
    sections_buffered = sections.buffer(0.5 * buffer_length, cap_style=2)

    # Export
    if export_buffered_sections:
        sections_buffered.to_file("sections_buffered.shp")

    # Compute pixel area
    pixel_area = watermask.transform[0] * np.abs(watermask.transform[4])

    for section_index in sections.index:

        # Mask the water mask with the buffer of current section
        section_buffered = sections_buffered.loc[section_index]
        if section_buffered.is_empty:
            updated_sections.loc[section_index, "width"] = np.nan

        else:
            try:
                out_image, out_transform = mask(watermask, shapes=[section_buffered], crop=True, nodata=0)

                # Count number of cells
                buffer_pixels = np.sum(out_image == 0) + np.sum(out_image > 0)

                # Count number of water cells
                water_pixels = np.sum(out_image > 0)
                water_area = water_pixels * pixel_area

                # Compute widths from area / buffer_length
                effective_width = water_area / buffer_length
                if min_width is not None:
                    if effective_width < min_width:
                        effective_width = min_width

                # Update with value in the GeoDataFrame
                updated_sections.loc[section_index, "width"] = effective_width
                if buffer_pixels == water_pixels:
                    updated_sections.loc[section_index, "flg_bufful"] = 1
                else:
                    updated_sections.loc[section_index, "flg_bufful"] = 0

            except Exception:
                updated_sections.loc[section_index, "width"] = np.nan

    # Print the dry sections
    if bool_print_dry:
        dry_sections = updated_sections[updated_sections["width"] < 1e-6]
        for section_index in range(dry_sections.shape[0]):
            dry_section = dry_sections.iloc[section_index, :]
            print("Dry section: %i (ID=%s)" % (section_index, dry_section[index_attr]))

    return updated_sections, sections_buffered


def compute_widths_from_single_watermask_scenario11(watermask, sections, buffer_length=25.0, index_attr="index",
                                                    **kwargs):
    """Compute the widths for a list of cross-sections using a watermask

        Parameters
        ----------
        index_attr : str
            Name of the attribute that contains indexes in the GeoDataFrame.
        watermask : rasterio.DatasetReader
            Raster of the water mask (any positive value is considered as water).
        sections : geopandas.GeoDataFrame
            GeoDataFrame containing (at least) the cross-sections geometry and the length and index attributes.
        buffer_length : float
            Length of the buffer to apply to cross-sections.
        kwargs : dict
            Other keyword arguments:
            bool_print_dry : bool
                If true, print out information on possible dry sections
            min_width : float
                Value of the minimal width.
            fname_buffered_section : str
                Path to the output file that will contain the buffered cross-sections. Default is None (no output).
        """

    # Parse extra argument keywords
    bool_print_dry = False
    if "bool_print_dry" in kwargs:
        bool_print_dry = kwargs["bool_print_dry"]
    min_width = None
    if "min_width" in kwargs:
        min_width = kwargs["min_width"]
    export_buffered_sections = False
    if "export_buffered_sections" in kwargs:
        export_buffered_sections = kwargs["export_buffered_sections"]

    # Check classes of input parameters
    if not isinstance(sections, gpd.GeoDataFrame):
        raise ValueError("sections must be a geopandas GeoDataFrame")
    if not isinstance(watermask, rio.DatasetReader):
        raise ValueError("watermask must be a rasterio DatasetReader")

    if min_width is not None:
        if not isinstance(min_width, int) and not isinstance(min_width, float):
            raise ValueError("min_width must be a number")

    if not isinstance(export_buffered_sections, bool):
        raise ValueError("export_buffered_sections must be True or False")

    # Create updated_sections GeoDataFrame (result of this function)
    updated_sections = sections.copy()
    updated_sections.insert(len(updated_sections.columns) - 1, "width",
                            np.nan)  # Add a column to contain estimated width
    updated_sections.insert(len(updated_sections.columns) - 1, "flg_bufful",
                            np.nan)  # Add a column to contain flag indicating if buffer is full of water (and so potentially sections is too short)
    updated_sections.insert(len(updated_sections.columns) - 1, "beta",
                            np.nan)  # Add a column to contain fraction of buffer area intersecting other buffer
    updated_sections.insert(len(updated_sections.columns) - 1, "nb_banks",
                            np.nan)  # Add a column to contain number of river banks in buffer

    # Project sections to EPSG 3857 if necessary (to get metric distances)
    if sections.crs.to_epsg() == 4326:
        print("Inputs in epsg:4326 are projected to epsg:3857, not effective away from equator.")
        sections = sections.to_crs(epsg=3857)

    # Apply buffer to sections
    sections_buffered = sections.buffer(0.5 * buffer_length, cap_style=2)

    # Export
    if export_buffered_sections:
        sections_buffered.to_file("sections_buffered.shp")

    # Compute pixel area
    pixel_area = watermask.transform[0] * np.abs(watermask.transform[4])

    l_shape = []
    l_buffer_waterarea = []
    l_nb_banks = []
    for section_index in sections.index:

        # Mask the water mask with the buffer of current section
        section_buffered = sections_buffered.loc[section_index]

        if section_buffered.is_empty:
            updated_sections.loc[section_index, "width"] = np.nan
            l_shape.append(MultiPolygon())
            l_buffer_waterarea.append(0.0)
            l_nb_banks.append(0.0)

        else:
            try:
                out_image, out_transform = mask(watermask, shapes=[section_buffered], crop=True, nodata=0)

                # Count number of cells
                buffer_pixels = np.sum(out_image == 0) + np.sum(out_image > 0)

                # Count number of water cells
                water_pixels = np.sum(out_image > 0)
                water_area = water_pixels * pixel_area

                # Compute widths from area / buffer_length
                effective_width = water_area / buffer_length
                if min_width is not None:
                    if effective_width < min_width:
                        effective_width = min_width

                # Update with value in the GeoDataFrame
                updated_sections.loc[section_index, "width"] = effective_width
                if buffer_pixels == water_pixels:
                    updated_sections.loc[section_index, "flg_bufful"] = 1
                else:
                    updated_sections.loc[section_index, "flg_bufful"] = 0

                # Compute water buffer polygon
                l_all_polygons = []
                il_i = 0
                for feat, value in shapes(out_image, mask=(out_image > 0), transform=out_transform):
                    l_polygons = []
                    l_values = []
                    for coords in feat["coordinates"]:
                        l_polygons.append(Polygon(coords))
                    if len(l_polygons) > 1:
                        big_pol = l_polygons[0]
                        small_pol = MultiPolygon(l_polygons[1:])
                        polygon = big_pol.difference(small_pol)
                    else:
                        polygon = l_polygons[0]
                    l_all_polygons.append(polygon)
                    l_values.append(value)
                    il_i += 1
                if len(l_all_polygons) > 1:
                    l_shape.append(MultiPolygon(l_all_polygons))
                    l_buffer_waterarea.append(water_area)
                    l_nb_banks.append(2 * len(l_all_polygons))
                else:
                    l_shape.append(MultiPolygon())
                    l_buffer_waterarea.append(water_area)
                    l_nb_banks.append(2.0)

            except Exception:
                updated_sections.loc[section_index, "width"] = np.nan
                l_shape.append(MultiPolygon())
                l_buffer_waterarea.append(0.0)
                l_nb_banks.append(0.0)

    # Gather waterbody details for each buffer
    gdf_waterbuffer = gpd.GeoDataFrame(
        {"water_area": l_buffer_waterarea,
         "nb_banks": l_nb_banks,
         "intersect_area": 0.,
         "beta": 0.},
        index=sections.index,
        geometry=gpd.GeoSeries(l_shape, crs=sections.crs),
        crs=sections.crs
    )

    # Quantify intersection between buffer shapes
    for index in gdf_waterbuffer.index:
        if gdf_waterbuffer.at[index, "geometry"] is not None:
            geom = gdf_waterbuffer.at[index, "geometry"]

            gser_wrk = gdf_waterbuffer["geometry"].copy(deep=True)
            gser_wrk.drop(labels=index, inplace=True)

            ser_buffer_intersection = gser_wrk.intersection(geom)
            ser_buffer_intersection_areatot = ser_buffer_intersection.area
            gdf_waterbuffer.at[index, "intersect_area"] = ser_buffer_intersection_areatot.sum()

            if gdf_waterbuffer.at[index, "water_area"] != 0:
                beta = gdf_waterbuffer.at[index, "intersect_area"] / gdf_waterbuffer.at[index, "water_area"]
            else:
                beta = np.nan

            if np.isnan(beta) or np.isinf(beta):
                beta = 0.0
            gdf_waterbuffer.at[index, "beta"] = beta
    gdf_waterbuffer["flg_bufful"] = updated_sections["flg_bufful"]
    updated_sections["beta"] = gdf_waterbuffer["beta"]

    # Get waterbody banks number
    updated_sections["nb_banks"] = gdf_waterbuffer["nb_banks"]

    # Print the dry sections
    if bool_print_dry:
        dry_sections = updated_sections[updated_sections["width"] < 1e-6]
        for section_index in range(dry_sections.shape[0]):
            dry_section = dry_sections.iloc[section_index, :]
            print("Dry section: %i (ID=%s)" % (section_index, dry_section[index_attr]))

    return updated_sections, sections_buffered


def compute_widths_from_watermasks_collection(scenario, watermask_fnames, sections, buffer_length=25.0,
                                              index_attr="index",
                                              **kwargs):
    """Compute the widths for a list of cross-sections using a collection of watermasks

        Parameters
        ----------
        scenario : int
        watermask_fnames : str
            Paths to the watermasks
        sections : geopandas.GeoDataFrame
            GeoDataFrame containing (at least) the cross-sections geometry and the length and index attributes.
        buffer_length : float
            Length of the buffer to apply to cross-sections.
        index_attr : str
            Name of the attribute that contains indexes in the GeoDataFrame.
        kwargs : dict
            Other keyword arguments:
            output_dir : str
                Path to the output directory. Default is None,
                i.e. output files will be created in the same directory as the watermasks files.
            min_width : float
                Value of the minimal width.
            fname_buffered_section : str
                Path to the output file that will contain the buffered cross-sections. Default is None (no output).
        """

    # Parse extra keyword arguments
    output_dir = None
    if "output_dir" in kwargs:
        output_dir = kwargs["output_dir"]

    # CHECK-UP
    if not isinstance(output_dir, str):
        raise ValueError("output_dir must be a string")

    for watermask_fname in watermask_fnames:

        # Open current watermask raster
        watermask = rio.open(watermask_fname)

        # Compute widths
        updated_sections, _ = compute_widths_from_single_watermask(scenario,
                                                                   watermask,
                                                                   sections,
                                                                   buffer_length=buffer_length,
                                                                   index_attr=index_attr,
                                                                   **kwargs)

        # Export updated sections
        if output_dir is None:
            output_fname = "%s_widths.shp" % os.path.splitext(watermask_fname)[0]
        else:
            basename = "%s_widths.shp" % os.path.splitext(os.path.basename(watermask_fname))[0]
            output_fname = os.path.join(output_dir, basename)
        updated_sections.to_file(output_fname)
