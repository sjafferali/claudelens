import { useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/common';

export default function Projects() {
  const { projectId } = useParams();

  if (projectId) {
    return <ProjectDetail projectId={projectId} />;
  }

  return <ProjectsList />;
}

function ProjectsList() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Projects</h2>
        <p className="text-muted-foreground">
          Manage and explore your Claude projects
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i} className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle>Project {i}</CardTitle>
              <CardDescription>/path/to/project{i}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Sessions</span>
                  <span className="font-medium">124</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Messages</span>
                  <span className="font-medium">1,423</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Cost</span>
                  <span className="font-medium">$12.45</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ProjectDetail({ projectId }: { projectId: string }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Project {projectId}</h2>
        <p className="text-muted-foreground">
          /path/to/project/{projectId}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Project Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Detailed project statistics and session list will be displayed here
          </p>
        </CardContent>
      </Card>
    </div>
  );
}