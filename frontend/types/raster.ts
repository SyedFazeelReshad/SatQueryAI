export interface RasterInfo {
  width: number;
  height: number;
  count: number;
  dtype: string;
  crs: string | null;
  crs_epsg: number | null;
  bounds: { left: number; bottom: number; right: number; top: number };
  resolution_x: number;
  resolution_y: number;
  gsd_m: number | null;
  nodata: number | null;
  file_size_bytes: number;
  format: string;
  warnings: string[];
}
