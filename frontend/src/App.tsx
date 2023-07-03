import "./App.css";

import CurrentUser from "./components/CurrentUser";
import LoginForm from "./components/LoginForm";
import ProjectForm from "./components/ProjectForm/ProjectForm";
import RegistrationForm from "./components/RegistrationForm";

function App() {
  return (
    <div className="App">
      <RegistrationForm />
      <LoginForm />
      <CurrentUser />
      <ProjectForm />
    </div>
  );
}

export default App;
