import React from 'react';
import { MONTHS, monthName, yearOptions } from '../utils/dates';

function PeriodSelect({ month, year, onMonthChange, onYearChange, monthFormat = 'long' }) {
  return (
    <>
      <select
        aria-label="Month"
        value={month}
        onChange={(e) => onMonthChange(parseInt(e.target.value, 10))}
      >
        {MONTHS.map(m => (
          <option key={m} value={m}>{monthName(m, monthFormat)}</option>
        ))}
      </select>
      <select
        aria-label="Year"
        value={year}
        onChange={(e) => onYearChange(parseInt(e.target.value, 10))}
      >
        {yearOptions().map(y => (
          <option key={y} value={y}>{y}</option>
        ))}
      </select>
    </>
  );
}

export default PeriodSelect;
