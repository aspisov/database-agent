import logging
import traceback
import typing as tp

import pandas as pd


def query_results_to_dataframe(
    query_results: dict[str, tp.Any] | None
) -> pd.DataFrame | None:
    """
    Convert database query results to a pandas DataFrame.

    Args:
        query_results: Results from database query execution

    Returns:
        DataFrame with the results, or None if conversion fails
    """
    if query_results is None:
        return None

    if not query_results.get("success", False):
        return None

    if "rows" not in query_results:
        return None

    try:
        # Create DataFrame from rows
        df = pd.DataFrame(query_results["rows"])
        return df
    except Exception as e:
        logging.exception(f"Error converting query results to dataframe: {e}")
        logging.exception(traceback.format_exc())
        return None
