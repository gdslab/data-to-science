import { AxiosResponse } from 'axios';
import { useLoaderData } from 'react-router';
import { ResponsiveCalendar } from '@nivo/calendar';
import { ResponsiveLine } from '@nivo/line';

import { User } from '../../../AuthContext';

import api from '../../../api';

const MONTH_ABBREVS = {
  0: 'Jan',
  1: 'Feb',
  2: 'Mar',
  3: 'Apr',
  4: 'May',
  5: 'Jun',
  6: 'Jul',
  7: 'Aug',
  8: 'Sep',
  9: 'Oct',
  10: 'Nov',
  11: 'Dec',
};

export async function loader() {
  const response: AxiosResponse<User[]> = await api.get('/admin/users');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

/**
 * Return count of created users by date.
 * @param data Array of users.
 * @returns Each unique creation date and a count for users created on that date.
 */
function countByDate(data: User[]): { day: string; value: number }[] {
  const dateCounts: { [key: string]: number } = {};

  data.forEach((item) => {
    const date = new Date(item.created_at).toISOString().slice(0, 10);
    dateCounts[date] = (dateCounts[date] || 0) + 1;
  });

  const result = Object.entries(dateCounts).map(([day, value]) => ({
    day,
    value,
  }));

  return result;
}

/**
 * Return first date a user was created.
 * @param data Array of users.
 * @returns First date a user was created.
 */
function getStartDate(data: User[]): string {
  let startDate = new Date(data[0].created_at);

  data.forEach((item) => {
    const currentDate = new Date(item.created_at);
    if (currentDate < startDate) {
      startDate = currentDate;
    }
  });

  const formattedStartDate = startDate.toISOString().slice(0, 10);

  return formattedStartDate;
}

/**
 * Return accumulative count of users by month.
 * @param data Array of users.
 * @param currentYear Accumulative count will be for this year.
 * @returns Accumulative count of users by month.
 */
function accumCountByMonth(
  data: User[],
  currentYear: number
): { x: string; y: number }[] {
  // Construct array of user accounts created within currentYear
  const filteredByYear = data.filter(
    (item) => new Date(item.created_at).getFullYear() === currentYear
  );
  // Count how many users were added each month in currentYear
  const monthCounts: { [key: string]: number } = {};
  for (const item of filteredByYear) {
    const date = new Date(item.created_at);
    const month = date.getMonth();
    monthCounts[month] = (monthCounts[month] || 0) + 1;
  }

  // Calculate accumulative growth
  let accumCount = 0;
  const accumResult: { x: string; y: number }[] = [];
  for (let month = 0; month < 12; month++) {
    accumCount += monthCounts[month] || 0;
    accumResult.push({
      x: MONTH_ABBREVS[month],
      y: accumCount,
    });
  }

  return accumResult;
}

export default function DashboardCharts() {
  const users = useLoaderData() as User[];

  if (users.length === 0) {
    return <section className="w-full bg-white">No users</section>;
  }

  const currentYear = new Date().getFullYear();

  // Find earliest created_at year
  const earliestYear = users.reduce(
    (minYear, user) =>
      Math.min(minYear, new Date(user.created_at).getFullYear()),
    Infinity
  );

  // Create array of years starting with earliest year to current year
  const years = Array.from(
    { length: currentYear - earliestYear + 1 },
    (_, i) => earliestYear + i
  );

  // Calculate accumulative user growth per month over every year
  const allYears: { id: string; data: { x: string; y: number }[] }[] = [];
  years.forEach((year) => {
    allYears.push({
      id: year.toString(),
      data: accumCountByMonth(users, year),
    });
  });

  return (
    <section className="w-full h-full bg-white p-4">
      <div className="h-1/2 py-8">
        <h2>Signup Activity Calendar</h2>
        <ResponsiveCalendar
          data={countByDate(users)}
          from={getStartDate(users)}
          to={new Date().toISOString().slice(0, 10)}
          emptyColor="#eeeeee"
          colors={['#61cdbb', '#97e3d5', '#e8c1a0', '#f47560']}
          margin={{ top: 40, right: 40, bottom: 40, left: 40 }}
          yearSpacing={40}
          monthBorderColor="#d1d5db"
          dayBorderWidth={2}
          dayBorderColor="#ffffff"
          legends={[
            {
              anchor: 'bottom-right',
              direction: 'row',
              translateY: 36,
              itemCount: 4,
              itemWidth: 42,
              itemHeight: 36,
              itemsSpacing: 14,
              itemDirection: 'right-to-left',
            },
          ]}
        />
      </div>
      <div className="h-1/2 py-8">
        <h2>{`${earliestYear} - ${currentYear} User Growth`}</h2>
        <ResponsiveLine
          data={allYears}
          margin={{ top: 50, right: 110, bottom: 50, left: 60 }}
          xScale={{ type: 'point' }}
          yScale={{
            type: 'linear',
            min: 'auto',
            max: 'auto',
            stacked: true,
            reverse: false,
          }}
          yFormat=" >-.2f"
          axisTop={null}
          axisRight={null}
          axisBottom={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: 'Month',
            legendOffset: 36,
            legendPosition: 'middle',
            truncateTickAt: 0,
          }}
          axisLeft={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: 'Total Users',
            legendOffset: -40,
            legendPosition: 'middle',
            truncateTickAt: 0,
            format: (val) => (Math.trunc(val) === val ? val : ''),
          }}
          pointSize={10}
          pointColor={{ theme: 'background' }}
          pointBorderWidth={2}
          pointBorderColor={{ from: 'serieColor' }}
          pointLabel="data.yFormatted"
          pointLabelYOffset={-12}
          enableTouchCrosshair={true}
          useMesh={true}
          legends={[
            {
              anchor: 'bottom-right',
              direction: 'column',
              justify: false,
              translateX: 100,
              translateY: 0,
              itemsSpacing: 0,
              itemDirection: 'left-to-right',
              itemWidth: 80,
              itemHeight: 20,
              itemOpacity: 0.75,
              symbolSize: 12,
              symbolShape: 'circle',
              symbolBorderColor: 'rgba(0, 0, 0, .5)',
              effects: [
                {
                  on: 'hover',
                  style: {
                    itemBackground: 'rgba(0, 0, 0, .03)',
                    itemOpacity: 1,
                  },
                },
              ],
            },
          ]}
        />
      </div>
    </section>
  );
}
