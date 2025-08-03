import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  ConfirmDialog,
} from '@/components/common';
import { useProjects, useProject, useDeleteProject } from '@/hooks/useProjects';
import { useSessions } from '@/hooks/useSessions';
import { formatDistanceToNow } from 'date-fns';
import { Loader2, FolderOpen, MessageSquare, Trash2 } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { Project } from '@/api/types';

export default function Projects() {
  const { projectId } = useParams();

  if (projectId) {
    return <ProjectDetail projectId={projectId} />;
  }

  return <ProjectsList />;
}

function ProjectsList() {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(0);
  const [deleteProjectId, setDeleteProjectId] = useState<string | null>(null);
  const [deleteProjectName, setDeleteProjectName] = useState<string>('');
  const [deleteProjectStats, setDeleteProjectStats] = useState<{
    session_count: number;
    message_count: number;
  } | null>(null);
  const pageSize = 12;

  const { data, isLoading, error, refetch } = useProjects({
    skip: currentPage * pageSize,
    limit: pageSize,
    sortBy: 'updated_at',
    sortOrder: 'desc',
  });
  const deleteProject = useDeleteProject();

  const handleDelete = async () => {
    if (!deleteProjectId) return;

    try {
      await deleteProject.mutateAsync({
        projectId: deleteProjectId,
        cascade: true,
      });
      toast.success('Project deleted successfully');
      refetch();
    } catch (error) {
      toast.error('Failed to delete project');
      console.error('Delete project error:', error);
    }
    setDeleteProjectId(null);
  };

  const handleDeleteClick = (e: React.MouseEvent, project: Project) => {
    e.stopPropagation(); // Prevent navigation to project detail
    setDeleteProjectId(project._id);
    setDeleteProjectName(project.name);
    setDeleteProjectStats(project.stats || null);
  };

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Projects</h2>
          <p className="text-muted-foreground">
            Manage and explore your Claude projects
          </p>
        </div>
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">Failed to load projects</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Projects</h2>
        <p className="text-muted-foreground">
          Manage and explore your Claude projects
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data?.items.length === 0 ? (
              <Card className="col-span-full">
                <CardContent className="p-12 text-center">
                  <p className="text-muted-foreground">No projects found</p>
                </CardContent>
              </Card>
            ) : (
              data?.items.map((project) => (
                <Card
                  key={project._id}
                  onClick={() => navigate(`/projects/${project._id}`)}
                  className="cursor-pointer hover:shadow-lg transition-shadow relative"
                >
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => handleDeleteClick(e, project)}
                    className="absolute top-2 right-2 p-2 hover:bg-destructive/10"
                    title="Delete project"
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 pr-8">
                      <FolderOpen className="h-4 w-4" />
                      {project.name}
                    </CardTitle>
                    <CardDescription className="truncate" title={project.path}>
                      {project.path}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          Sessions
                        </span>
                        <span className="font-medium">
                          {project.stats?.session_count || 0}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">Messages</span>
                        <span className="font-medium">
                          {project.stats?.message_count || 0}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">
                          Last updated
                        </span>
                        <span className="font-medium text-xs">
                          {formatDistanceToNow(new Date(project.updatedAt), {
                            addSuffix: true,
                          })}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {data && data.items.length > 0 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {currentPage * pageSize + 1} to{' '}
                {Math.min((currentPage + 1) * pageSize, data.total)} of{' '}
                {data.total}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 0}
                  className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={!data.has_more}
                  className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      <ConfirmDialog
        isOpen={!!deleteProjectId}
        title="Delete Project"
        message={
          <div>
            <p>
              Are you sure you want to delete the project "{deleteProjectName}"?
            </p>
            <p className="mt-2 text-sm">This will permanently delete:</p>
            <ul className="mt-1 ml-4 text-sm list-disc">
              <li>All {deleteProjectStats?.session_count || 0} sessions</li>
              <li>All {deleteProjectStats?.message_count || 0} messages</li>
              <li>The project configuration</li>
            </ul>
            <p className="mt-2 text-sm font-semibold">
              This action cannot be undone.
            </p>
          </div>
        }
        confirmLabel="Delete Project"
        onConfirm={handleDelete}
        onCancel={() => setDeleteProjectId(null)}
      />
    </div>
  );
}

function ProjectDetail({ projectId }: { projectId: string }) {
  const navigate = useNavigate();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const { data: project, isLoading: projectLoading } = useProject(projectId);
  const { data: sessions, isLoading: sessionsLoading } = useSessions({
    projectId,
    limit: 10,
    sortBy: 'started_at',
    sortOrder: 'desc',
  });
  const deleteProject = useDeleteProject();

  const handleDelete = async () => {
    try {
      await deleteProject.mutateAsync({ projectId, cascade: true });
      toast.success('Project deleted successfully');
      navigate('/projects');
    } catch (error) {
      toast.error('Failed to delete project');
      console.error('Delete project error:', error);
    }
    setShowDeleteDialog(false);
  };

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Project Not Found
          </h2>
          <p className="text-muted-foreground">
            This project could not be found.
          </p>
        </div>
        <button
          onClick={() => navigate('/projects')}
          className="text-sm text-primary hover:underline"
        >
          ← Back to projects
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <button
          onClick={() => navigate('/projects')}
          className="text-sm text-muted-foreground hover:text-foreground mb-2 flex items-center gap-1"
        >
          ← Back to projects
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <FolderOpen className="h-8 w-8" />
              {project.name}
            </h2>
            <p className="text-muted-foreground">{project.path}</p>
            {project.description && (
              <p className="mt-2 text-sm">{project.description}</p>
            )}
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowDeleteDialog(true)}
            className="flex items-center gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Delete Project
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Sessions
            </CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {project.stats?.session_count || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Messages
            </CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {project.stats?.message_count || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatDistanceToNow(new Date(project.updatedAt), {
                addSuffix: true,
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
          <CardDescription>
            Latest conversation sessions in this project
          </CardDescription>
        </CardHeader>
        <CardContent>
          {sessionsLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : sessions?.items.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">
              No sessions found for this project
            </p>
          ) : (
            <div className="space-y-4">
              {sessions?.items.map((session) => (
                <div
                  key={session._id}
                  onClick={() => navigate(`/sessions/${session._id}`)}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                >
                  <div className="space-y-1 flex-1">
                    <p className="font-medium">
                      {session.summary ||
                        `Session ${session.sessionId.slice(0, 8)}...`}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {session.messageCount} messages •
                      {formatDistanceToNow(new Date(session.startedAt), {
                        addSuffix: true,
                      })}
                    </p>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {session.totalCost
                      ? `$${session.totalCost.toFixed(2)}`
                      : 'N/A'}
                  </div>
                </div>
              ))}

              {sessions && sessions.total > 10 && (
                <button
                  onClick={() => navigate(`/sessions?project_id=${projectId}`)}
                  className="w-full py-2 text-sm text-primary hover:underline"
                >
                  View all {sessions.total} sessions →
                </button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        title="Delete Project"
        message={
          <div>
            <p>Are you sure you want to delete the project "{project.name}"?</p>
            <p className="mt-2 text-sm">This will permanently delete:</p>
            <ul className="mt-1 ml-4 text-sm list-disc">
              <li>All {project.stats?.session_count || 0} sessions</li>
              <li>All {project.stats?.message_count || 0} messages</li>
              <li>The project configuration</li>
            </ul>
            <p className="mt-2 text-sm font-semibold">
              This action cannot be undone.
            </p>
          </div>
        }
        confirmLabel="Delete Project"
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteDialog(false)}
      />
    </div>
  );
}
