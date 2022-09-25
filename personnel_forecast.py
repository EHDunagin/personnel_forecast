import pandas as pd
from tkinter import filedialog


def date_range(start, periods):
    """
    Input ->
    start - date from which to start projection. Precision at a monthly level will be used.
    periods - integer indicating number of months to project
    Output -> DataFrame of month start and end dates

    Creates and returns DataFrame of month start and end dates from start date and number of months.
    """

    date_df = pd.DataFrame(
        data={
            "month_starts": pd.date_range(
                start=start.replace(day=1),
                periods=periods,
                freq="MS",
            ),
            "month_ends": pd.date_range(
                start=start,
                periods=periods,
                freq="M",
            ),
        }
    )

    return date_df


def personnel_forecast(date_df, fringe, positions):
    """
    Input -> DataFrames with input information to use to generate forecast
        date_df: DataFrame with start and end dates of periods in forecast
        fringe: floating point fringe as percentage of salary
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

    Output -> DataFrame of forecast of expense by employee for each month from start to end (based on number of months)
    of forecast range with rows for salary bonus commission and fringe.
    """


    # Fill in missing employee start and end dates with min or max timestamps
    positions["start_date"] = positions["start_date"].fillna(value=pd.Timestamp.min)
    positions["end_date"] = positions["end_date"].fillna(value=pd.Timestamp.max)

    # Calculate monthly salary, bonus, commission, and fringe amounts. Shifts these values from columns to rows.
    forecast_df = positions.assign(
        salary=positions["salary_annual"] / 12,
        bonus=positions["salary_annual"] * positions["bonus_rate"] / 12,
        commission=positions["salary_annual"] * positions["commission_rate"] / 12,
        fringe=positions["salary_annual"] * fringe / 12,
    ).melt(
        id_vars=[
            "position_id",
            "position_title",
            "department",
            "employee_id",
            "employee_name",
            "start_date",
            "end_date",
        ],
        value_vars=["salary", "bonus", "commission", "fringe"],
        var_name="expense_type",
        value_name="expense_amount",
    )

    # Filter to exclude amounts of 0
    forecast_df = forecast_df[forecast_df["expense_amount"] != 0]

    # Cross join personnel info to date DF.
    forecast_df = date_df.merge(forecast_df, how="cross")

    # Filter to exclude months before start or after end of specific employee
    forecast_df = forecast_df[
        (forecast_df["start_date"] <= forecast_df["month_ends"])
        & (forecast_df["end_date"] >= forecast_df["month_starts"])
    ]

    forecast_df["item"] = forecast_df["expense_type"]

    # Add headcount column with 1 in headcount on "salary" line iff start date is before and end date is after end of month.
    forecast_df["headcount"] = (
        (forecast_df["start_date"] <= forecast_df["month_ends"])
        & (forecast_df["end_date"] >= forecast_df["month_ends"])
        & (forecast_df["expense_type"] == "salary")
    ).astype("int")

    return forecast_df


def related_forecast(date_df, related):
    """
    Input -> DataFrames with input information to use to generate forecast
        date_df: DataFrame with start and end dates of periods in forecast
        related: information about personnel related expense to forecast includes columns
            position_id
            position_title
            department
            employee_id
            employee_name
            item (description)
            expense_type
            amount_annual
            start_date
            end_date
    Output -> DataFrame of forecast of personnel related expense by employee for each month from start to end
    (based on number of months) of forecast range with rows each personnel related item.
    """
    # Fill in missing employee start and end dates with min or min timestamps
    related["start_date"] = related["start_date"].fillna(value=pd.Timestamp.min)
    related["end_date"] = related["end_date"].fillna(value=pd.Timestamp.max)

    # Calculate monthly expense amount for personnel related items.
    forecast_df = related.assign(expense_amount=related["amount_annual"] / 12)

    # Filter to exclude amounts of 0
    forecast_df = forecast_df[forecast_df["expense_amount"] != 0]

    # Cross join personnel info to date DF.
    forecast_df = date_df.merge(forecast_df, how="cross")

    # Filter to exclude months before start or after end of specific expense
    forecast_df = forecast_df[
        (forecast_df["start_date"] <= forecast_df["month_ends"])
        & (forecast_df["end_date"] >= forecast_df["month_starts"])
    ]

    return forecast_df


def onetime_forecast(onetime):
    """
    Input -> DataFrames with input information to use to generate forecast
        date_df: DataFrame with start and end dates of periods in forecast
        related: information about personnel related expense to forecast includes columns
            position_id
            position_title
            department
            employee_id
            employee_name
            item (description)
            expense_type
            expense_amount
            expense_date
    Output -> DataFrame of forecast of one time personnel expenses by employee fwith rows each item.
    """
    forecast_df = onetime

    # Create date fields to align with other dataframes with start and end dates for the month of each item
    forecast_df["month_starts"] = forecast_df["expense_date"] - pd.offsets.MonthBegin(1)
    forecast_df["month_ends"] = forecast_df["expense_date"] - pd.offsets.MonthEnd(-1)
    forecast_df["start_date"] = forecast_df["month_starts"]
    forecast_df["end_date"] = forecast_df["month_ends"]

    return forecast_df


def adjust_expense(forecast, inflation):
    """
    Input ->
        forecast: DataFrame of forecast expenses by date with relevant period information
        inflation: expected inflation rates includes columns "inflation_date" and "inflation_rate" (from start)
    Output ->
        DataFrame of forecast expense prorated for start and end dates, and scaled for inflation
    """
    forecast_df = forecast

    # Calculates proration of month from start and end.
    forecast_df["proration"] = (
        (
            forecast_df[["end_date", "month_ends"]].min(axis=1)
            - forecast_df[["start_date", "month_starts"]].max(axis=1)
        ).dt.days
        + 1
    ) / ((forecast_df["month_ends"] - forecast_df["month_starts"]).dt.days + 1)

    # Sort by month_starts to allow asof merge
    forecast_df = forecast_df.sort_values(by="month_starts")

    # Join inflation data. Fills any unmatched periods with 1 (no inflation from input amount)
    forecast_df = pd.merge_asof(
        forecast_df, inflation, left_on="month_starts", right_on="inflation_date"
    )
    forecast_df["inflation_rate"] = forecast_df["inflation_rate"].fillna(value=1)

    # Calculates forecast amount from monthly amount, proration, and applicable inflation.
    forecast_df["expense_amount"] = (
        forecast_df["expense_amount"]
        * forecast_df["proration"]
        * forecast_df["inflation_rate"]
    )

    return forecast_df


def get_inputs(fpath):
    """
    Input -> Filepath to Excel file with input info
    Output -> DataFrames with input information to use to generate forecast
    """
    settings = pd.read_excel(fpath, sheet_name="settings", index_col=0)
    positions = pd.read_excel(fpath, sheet_name="positions")
    related = pd.read_excel(fpath, sheet_name="related")
    onetime = pd.read_excel(fpath, sheet_name="onetime")
    inflation = pd.read_excel(fpath, sheet_name="inflation")

    return settings, positions, related, onetime, inflation


if __name__ == "__main__":
    # Prompt for filepath
    fpath = filedialog.askopenfilename(
        title="Select inputs file", filetypes=[("Microsoft Excel Worksheet", "*.xlsx")]
    )

    output_path = (
        filedialog.askdirectory(title="Select output directory ")
        + "/output_personnel_forecast.csv"
    )

    # Get inputs
    settings, positions, related, onetime, inflation = get_inputs(fpath)

    # Create date ranges
    date_df = date_range(
        settings.loc["start_date", "setting"], settings.loc["months", "setting"]
    )

    # Create pieces of forecast
    personnel_df = personnel_forecast(
        date_df, settings.loc["fringe", "setting"], positions
    )
    related_df = related_forecast(date_df, related)
    onetime_df = onetime_forecast(onetime)

    # Combine pieces of forecast
    forecast_df = pd.concat(
        [
            personnel_df[
                [
                    "month_starts",
                    "month_ends",
                    "position_id",
                    "position_title",
                    "department",
                    "employee_id",
                    "employee_name",
                    "start_date",
                    "end_date",
                    "expense_type",
                    "expense_amount",
                    "item",
                    "headcount",
                ]
            ],
            related_df[
                [
                    "month_starts",
                    "month_ends",
                    "position_id",
                    "position_title",
                    "department",
                    "employee_id",
                    "employee_name",
                    "start_date",
                    "end_date",
                    "expense_type",
                    "expense_amount",
                    "item",
                ]
            ],
            onetime_df[
                [
                    "month_starts",
                    "month_ends",
                    "position_id",
                    "position_title",
                    "department",
                    "employee_id",
                    "employee_name",
                    "start_date",
                    "end_date",
                    "expense_type",
                    "expense_amount",
                    "item",
                ]
            ],
        ]
    )

    # Prorate expense for start and end dates and apply inflation
    forecast_df = adjust_expense(forecast_df, inflation)

    forecast_df.to_csv(output_path)
