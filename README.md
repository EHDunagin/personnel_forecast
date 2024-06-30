# personnel_forecast
## Simple python model for personnel expense and headcount forecasting

Consists primarily of function **forecast** which uses information about period range, employees, fringe rate, and inflation
to generate a forecast of personnel expense and month end headcount.

The script is set up to read inputs from an Excel file structured like "personnel_sample.xlsx"and produce a .csv output if run on its own.
However the function could be used with similarly structured Pandas DataFrames to allow for pulling from a database or other sources.

### personnel_forecast.forecast(settings, positions, inflation)

For every month from month of start date specified in **settings** for number of months specified, generates a forecast of expense amount
for every employee in **positions** for the categories of salary, bonus, commission, and fringe. These amounts are prorated for the portion
of the month that the employee is active and scaled for inflation from **inflation**.

#### Parameters:
**settings :** Pandas DataFrame which includes start_date (first month to forecast), fringe (as percentage of salary), and months (number of periods in forecast)

|Type  |Name        |Description                |
|------|------------|---------------------------|
|Index |setting_name|Description of setting     |
|Column|setting     |Value of setting to be used|

**positions :**
|Type  |Name           |Description                           |
|------|---------------|--------------------------------------|
|Column|position_id    |Numeric ID for position               |
|Column|position_title |Title/description of job              |
|Column|department     |Department                            |
|Column|employee_id    |Employee ID                           |
|Column|employee_name  |Employee name                         |
|Column|salary_annual  |Annual Salary                         |
|Column|bonus_rate     |Bonus as percent of salary            |
|Column|commission_rate|Target commission as percent of salary|
|Column|start_date     |Date employee started in position     |
|Column|end_date       |Date employee finished position       |

Allows separate identification of employee and position to allow tracking of a single position when one employee is replaced by another, 
or a single employee if they change positions.

**inflation :**
|Type  |Name           |Description                                                 |
|------|---------------|------------------------------------------------------------|
|Column|inflation_date |Date from which inflation rate is effective                 |
|Column|inflation_rate |Rate at which to scale amounts calculated from input salary |
