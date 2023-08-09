import { useContext } from 'react';

import { Button, OutlineButton } from '../forms/CustomButtons';
import Card from '../Card';

import AuthContext from '../../AuthContext';
import HintText from '../HintText';

export default function Profile() {
  const { user } = useContext(AuthContext);
  return (
    <div className="h-full flex flex-wrap items-center justify-center">
      <div className="sm:w-full md:w-1/3 max-w-xl mx-4">
        <Card>
          <div>
            <div className="flex flex-col items-center">
              <span className="font-semibold">
                {user?.first_name} {user?.last_name}
              </span>
              <HintText>{user?.email}</HintText>
              <div className="h-24 w-24 bg-accent1 rounded-full"></div>
            </div>
            <div className="flex items-center justify-between gap-4">
              <div className="w-1/2">
                <Button type="submit">Save</Button>
              </div>
              <div className="w-1/2">
                <OutlineButton type="button">Cancel</OutlineButton>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
