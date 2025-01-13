import { IndoorProjectAPIResponse } from './IndoorProject';
import IndoorProjectCard from './IndoorProjectCard';

type IndoorProjectListProps = {
  indoorProjects: IndoorProjectAPIResponse;
};

export default function IndoorProjectList({ indoorProjects }: IndoorProjectListProps) {
  return (
    <div>
      <h1>Indoor Projects</h1>
      <div className="flex flex-1 flex-wrap gap-4 pb-24 overflow-y-auto">
        {indoorProjects.map((indoorProject) => (
          <div key={indoorProject.id} className="h-16 w-">
            <IndoorProjectCard indoorProject={indoorProject} />
          </div>
        ))}
      </div>
    </div>
  );
}
