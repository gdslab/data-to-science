import { DataProduct } from '../../Project';

export type RawDataSource =
  | { kind: 'none' }
  | { kind: 'named'; filename: string }
  | { kind: 'unavailable' };

/**
 * Resolve how a data product's raw data source should be displayed.
 *
 * - `none`: product was not generated from raw data (no raw_data_id).
 * - `named`: the source raw data upload is still present; show its filename.
 * - `unavailable`: product has a raw_data_id but the upload is gone
 *   (deactivated or purged), so no filename can be shown.
 */
export function resolveRawDataSource(
  dataProduct: DataProduct,
  rawDataFilenames: Map<string, string>
): RawDataSource {
  if (!dataProduct.raw_data_id) {
    return { kind: 'none' };
  }
  const filename = rawDataFilenames.get(dataProduct.raw_data_id);
  if (filename) {
    return { kind: 'named', filename };
  }
  return { kind: 'unavailable' };
}
