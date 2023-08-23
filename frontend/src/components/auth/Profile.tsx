import { useContext, useState } from 'react';
import { Formik, Form } from 'formik';
import { XMarkIcon } from '@heroicons/react/24/outline';

import { Button, OutlineButton } from '../forms/Buttons';
import Card from '../Card';
import CustomTextField from '../forms/CustomTextField';

import AuthContext from '../../AuthContext';
import HintText from '../HintText';
import CustomSelectField from '../forms/CustomSelectField';

export default function Profile() {
  const { user } = useContext(AuthContext);
  const [keywords, setKeywords] = useState<string[]>(['HTP', 'LiDAR', 'Ortho', 'UAS']);
  const [newKeyword, setNewKeyword] = useState('');

  function addKeyword(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    if (newKeyword) {
      setKeywords([...keywords, newKeyword]);
      setNewKeyword('');
    }
  }

  function removeKeyword(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    setKeywords(keywords.filter((kw) => kw != event.currentTarget.value));
  }

  function handleNewKeywordChange(event: React.ChangeEvent<HTMLInputElement>) {
    event.preventDefault();
    setNewKeyword(event.target.value);
  }

  return (
    <div className="bg-gradient-to-b from-accent1 from-20% to-white to-10%">
      <div className="h-full flex items-center justify-center">
        <div className="mt-16 h-full sm:w-full md:w-1/2 max-w-xl mx-4">
          <h1 className="ml-4 text-white">Edit Profile</h1>
          <Card>
            <div className="md:grid md:grid-flow-col md:grid-cols-6 md:gap-8">
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
                          <CustomTextField
                            label="First Name"
                            name="firstName"
                            required={false}
                          />
                        </div>
                        <div className="md:w-36 w-full">
                          <CustomTextField
                            label="Last Name"
                            name="lastName"
                            required={false}
                          />
                        </div>
                      </div>
                      <CustomTextField
                        label="Email"
                        name="email"
                        required={false}
                        disabled={true}
                      />
                      <Button size="sm">Change Password</Button>
                      <CustomSelectField
                        label="Expertise"
                        name="expertise"
                        options={[{ label: '', value: '' }]}
                      />
                      <div>
                        <HintText>Keywords of Interest</HintText>
                        <div className="flex flex-wrap gap-4 mt-2">
                          {keywords.map((keyword, i) => (
                            <div
                              key={`${keyword}-${i}`}
                              className="flex items-center gap-2 bg-gray-200 rounded-lg px-2 py-1"
                            >
                              {keyword}
                              <button
                                className="p-1 hover:bg-gray-300 hover:text-accent1"
                                type="button"
                                value={keyword}
                                onClick={removeKeyword}
                              >
                                <span className="sr-only">(Remove)</span>
                                <XMarkIcon className="h-4 w-4" />
                              </button>
                            </div>
                          ))}
                          <div className="flex items-center justify-between gap-2">
                            <input
                              className="border-2 border-gray-300 rounded-lg p-2"
                              type="text"
                              name="newKeyword"
                              placeholder="New keyword"
                              value={newKeyword}
                              onChange={handleNewKeywordChange}
                            />
                            <button
                              className="h-full bg-yellow-400 text-white font-bold rounded-lg px-4 py-2 hover:bg-yellow-500 ease-in-out duration-300"
                              onClick={addKeyword}
                            >
                              Add
                            </button>
                          </div>
                        </div>
                      </div>
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
