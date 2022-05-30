import unittest
import pandas as pd
import numpy as np
from personnel_forecast import forecast

class PersonnelTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.settings = pd.DataFrame(
            data={'setting': [pd.to_datetime('1/1/2022'), 0.25, 24]},
            index=['start_date', 'fringe', 'months']
        )

        self.positions = pd.DataFrame(
            data={
                "position_id": [1, 2, 3],
                "position_title": ['foo', 'bar', 'baz'],
                "department": ['a', 'a', 'b'],
                "employee_id": [4, 5, 6],
                "employee_name": ['red', 'green', 'blue'],
                "salary_annual": [100, 200, 300],
                "bonus_rate": [.1, .2, 0],
                "commission_rate": [0, .1, .2],
                "start_date": [np.NaN, pd.to_datetime('02/15/2022', format='%m/%d/%Y'), np.NaN],
                "end_date": [pd.to_datetime('02/15/2022', format='%m/%d/%Y'), np.NaN, np.NaN],
            }
        )
        
        self.inflation = pd.DataFrame(data={
            'inflation_date': [pd.to_datetime('01/01/2022', format='%m/%d/%Y'), pd.to_datetime('01/01/2023', format='%m/%d/%Y'), pd.to_datetime('01/01/2024', format='%m/%d/%Y')],
            'inflation_rate': [1, 1.05, 1.10]
        })

        self.df = forecast(
            self.settings, 
            self.positions,
            self.inflation
        )

        return super().setUp()

    def test_range_length(self):

        df = self.df
        # Salary only for single employee without start or end date
        self.assertEqual(len(df[(df['position_id'] == 3) & (df['expense_type'] == 'salary')]), 24)

    def test_end_length(self):

        df = self.df
        # Salary only for single employee with end date in range
        self.assertEqual(len(df[(df['position_id'] == 1) & (df['expense_type'] == 'salary')]), 2)

    def test_start_length(self):

        df = self.df
        # Salary only for single employee with start date
        self.assertEqual(len(df[(df['position_id'] == 2) & (df['expense_type'] == 'salary')]), 23)

    def test_end_proration(self):
        # salary for ended period
        df = self.df[(self.df['position_id'] == 1) & (self.df['expense_type'] == 'salary') & (self.df['month_starts'] == pd.to_datetime('02/01/2022', format='%m/%d/%Y'))]
        self.assertAlmostEqual(df.iloc[0, 10], (100 / 12) * (15/28))

    def test_start_proration(self):
        # salary for started period
        df = self.df[(self.df['position_id'] == 2) & (self.df['expense_type'] == 'salary') & (self.df['month_starts'] == pd.to_datetime('02/01/2022', format='%m/%d/%Y'))]
        self.assertAlmostEqual(df.iloc[0, 10], (200 / 12) * (14/28))

    # TODO Test bonus amount

    # TODO Test commission amount

    # TODO Test fringe amount

    # TODO Test inflation matching to periods

    # TODO Test headcound with starts and ends



if __name__ == '__main__':
    unittest.main()