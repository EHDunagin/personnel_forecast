import pandas as pd
import numpy as np


def forecast(settings, positions, inflation):
    """
    Input -> DataFrames with input information to use to generate forecast
        settings: contains start date, fringe rate, and months to forecast
        positions: information about positions to forecast includes columns
            position_id
            position_title
            department
            employee_id
            employee_name
            salary_annual
            bonus_rate
            commission_rate
            start_date
            end_date
        inflation: expected inflation rates includes columns "inflation_date" and "inflation_rate" (from start)
    Output -> DataFrame of forecast of expense by employee for each month from start to end (based on number of months)
    of forecast range with rows for salary bonus commission and fringe

    
    """
    # Creates DataFrame of month start and end dates from start date and number of months.
    date_df = pd.DataFrame(
        data={
            "month_starts": pd.date_range(
                start=settings.loc["start_date", "setting"].replace(day=1),
                periods=settings.loc["months", "setting"],
                freq="MS",
            ),
            "month_ends": pd.date_range(
                start=settings.loc["start_date", "setting"],
                periods=settings.loc["months", "setting"],
                freq="M",
            ),
        }
    )

    # TODO Calculates monthly salary, bonus, commission, and fringe amounts. Shifts these values from columns to rows.
    # TODO Cross joins personnel info to date DF.
    # TODO Calculates proration of month from start and end.
    # TODO Joins inflation data.
    # TODO Calculates forecast amount from monthly amount, proration, and applicable inflation.
    # TODO Add headcount column with 1 in headcount on "salary" line iff start date is before and end date is after end of month.

    breakpoint()
    # TODO return


def get_inputs(fpath):
    """
    Input -> Filepath to Excel file with input info
    Output -> DataFrames with input information to use to generate forecast
    """
    settings = pd.read_excel(fpath, sheet_name="settings", index_col=0)
    positions = pd.read_excel(fpath, sheet_name="positions")
    inflation = pd.read_excel(fpath, sheet_name="inflation")
    return settings, positions, inflation


if __name__ == "__main__":
    settings, positions, inflation = get_inputs(
        "C:/Users/dunag/python_projects/personnel_forecast/personnel_sample.xlsx"
    )
    forecast(settings, positions, inflation)
