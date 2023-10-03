import { useContext } from 'react';
import { Formik, Form } from 'formik';

import AuthContext from '../../../AuthContext';
import { Button, OutlineButton } from '../../Buttons';
import Card from '../../Card';
import HintText from '../../HintText';
import { TextField } from '../../InputFields';

export default function Profile() {
  const { user } = useContext(AuthContext);

  return (
    <div className="bg-gradient-to-b from-accent1 from-20% to-white to-10%">
      <div className="h-full flex items-center justify-center">
        <div className="mt-16 h-full sm:w-full md:w-1/2 max-w-xl mx-4">
          <h1 className="ml-4 text-white">Edit Profile</h1>
          <Card>
            <div className="grid grid-flow-col grid-cols-6 gap-8">
              {/* profile column */}
              <div className="col-span-2">
                <div className="flex flex-col items-center">
                  <span className="font-semibold">
                    {user?.first_name} {user?.last_name}
                  </span>
                  <HintText>{user?.email}</HintText>
                  <div className="h-24 w-24 mt-4 bg-accent1 rounded-full"></div>
                  <div className="mt-4">
                    <Button type="button" size="sm">
                      Upload New Photo
                    </Button>
                  </div>
                </div>
              </div>
              {/* form column */}
              <div className="col-span-4">
                <Formik
                  initialValues={{
                    firstName: user?.first_name,
                    lastName: user?.last_name,
                    email: user?.email,
                  }}
                  validationSchema={{}}
                  onSubmit={() => {}}
                >
                  {() => (
                    <Form className="flex flex-col gap-4">
                      <div className="flex flex-wrap justify-between w-full">
                        <div className="md:w-36 w-full">
                          <TextField
                            label="First Name"
                            name="firstName"
                            required={false}
                          />
                        </div>
                        <div className="md:w-36 w-full">
                          <TextField
                            label="Last Name"
                            name="lastName"
                            required={false}
                          />
                        </div>
                      </div>
                      <TextField
                        label="Email"
                        name="email"
                        required={false}
                        disabled={true}
                      />
                      <Button size="sm">Change Password</Button>
                      <div className="mt-4 flex items-center justify-between gap-4">
                        <div className="w-1/2">
                          <Button type="submit">Save</Button>
                        </div>
                        <div className="w-1/2">
                          <OutlineButton type="button">Cancel</OutlineButton>
                        </div>
                      </div>
                    </Form>
                  )}
                </Formik>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
