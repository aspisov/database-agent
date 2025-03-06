import typing as tp

import pandas as pd


def query_results_to_dataframe(
    query_results: dict[str, tp.Any] | None
) -> pd.DataFrame | None:
    """
    Convert query results to a pandas DataFrame.

    Args:
        query_results: The results from execute_query method

    Returns:
        pandas DataFrame containing the query results or None if conversion fails
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
        return None
