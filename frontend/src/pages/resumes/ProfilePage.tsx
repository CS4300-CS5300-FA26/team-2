import {
  useEffect,
  useState,
} from "react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";
import "./resumes.css";
import {
  ApiError,
  listResumes,
  parseResume,
  updateResumeFields,
  type Resume,
} from "./http";

export default function ProfilePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const resumeId = Number(id);

  const [resume, setResume] = useState<Resume | null>(null);
  const [skills, setSkills] = useState("");
  const [experience, setExperience] = useState("");
  const [education, setEducation] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    listResumes()
      .then((response) => {
        const selectedResume = response.results.find(
          (item) => item.id === resumeId,
        );

        if (!selectedResume) {
          setError("Resume not found");
          return;
        }

        setResume(selectedResume);
        setSkills(selectedResume.skills);
        setExperience(selectedResume.experience);
        setEducation(selectedResume.education);
      })
      .catch((requestError: ApiError) => {
        setError(requestError.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [resumeId]);

  async function runParser() {
    setWorking(true);
    setError(null);
    setDone(null);

    try {
      const parsedResume = await parseResume(resumeId);

      setResume(parsedResume);
      setSkills(parsedResume.skills);
      setExperience(parsedResume.experience);
      setEducation(parsedResume.education);
      setDone("Resume fields were created");
    } catch (requestError) {
      const apiError = requestError as ApiError;
      setError(apiError.message);
    } finally {
      setWorking(false);
    }
  }

  async function saveFields() {
    setWorking(true);
    setError(null);
    setDone(null);

    try {
      await updateResumeFields(
        resumeId,
        skills,
        experience,
        education,
      );

      navigate("/resumes/upload");
    } catch (requestError) {
      const apiError = requestError as ApiError;
      setError(apiError.message);
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="resumes-page">
      <p>
        <Link
          className="btn"
          to="/resumes/upload"
        >
          Back to resumes
        </Link>
      </p>

      <section className="card">
        <h1>Resume profile</h1>

        {loading && (
          <p className="muted">
            Loading resume
          </p>
        )}

        {error && (
          <p
            className="resumes-error"
            role="alert"
          >
            {error}
          </p>
        )}

        {done && (
          <p className="resumes-ok">
            {done}
          </p>
        )}

        {resume && (
          <>
            <p className="muted">
              Editing {resume.name}
            </p>

            <button
              type="button"
              className="btn"
              disabled={working}
              onClick={runParser}
            >
              {working
                ? "Working..."
                : "Parse resume with AI"}
            </button>

            <form
              className="resume-fields bare"
              onSubmit={(event) => {
                event.preventDefault();
                saveFields();
              }}
            >
              <label>
                Skills
                <textarea
                  rows={5}
                  value={skills}
                  disabled={working}
                  onChange={(event) => {
                    setSkills(event.target.value);
                  }}
                />
              </label>

              <label>
                Experience
                <textarea
                  rows={8}
                  value={experience}
                  disabled={working}
                  onChange={(event) => {
                    setExperience(event.target.value);
                  }}
                />
              </label>

              <label>
                Education
                <textarea
                  rows={5}
                  value={education}
                  disabled={working}
                  onChange={(event) => {
                    setEducation(event.target.value);
                  }}
                />
              </label>

              <button
                type="submit"
                className="btn"
                disabled={working}
              >
                Save changes
              </button>
            </form>

            <p className="muted small">
              AI parsing can make mistakes, so review the fields before saving
            </p>
          </>
        )}
      </section>
    </div>
  );
}