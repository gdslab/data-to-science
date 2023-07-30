import { useEffect, useState } from "react";
import axios from "axios";

export default function CurrentUser() {
  const [responseData, setResponseData] = useState(null);

  async function getCurrentUser() {
    try {
      const response = await axios.get("/api/v1/users/current", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });
      if (response) {
        console.log(response);
        setResponseData(response.data);
      } else {
        // do something
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        console.error(err);
      } else {
        console.error(err);
      }
    }
  }

  return (
    <div style={{ width: 450 }}>
      <fieldset>
        <legend>Get Current User</legend>
        <button onClick={() => getCurrentUser()}>Get current user</button>
        {responseData ? (
          <pre>{JSON.stringify(responseData, undefined, 2)}</pre>
        ) : (
          <div>Client not logged in</div>
        )}
      </fieldset>
    </div>
  );
}
