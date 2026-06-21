import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchWorklist, getSegmentationJobStatus, logout, runSegmentation } from '../api';

const OHIF_BASE_URL = import.meta.env.VITE_OHIF_BASE_URL || 'http://localhost:3030';
const TERMINAL_STATUSES = ['Succeeded', 'Failed', 'Error'];

export default function Worklist() {
  const [studies, setStudies] = useState([]);
  const [error, setError] = useState('');
  const [jobsByStudyId, setJobsByStudyId] = useState({});
  const navigate = useNavigate();
  const jobsByStudyIdRef = useRef(jobsByStudyId);
  jobsByStudyIdRef.current = jobsByStudyId;

  useEffect(() => {
    fetchWorklist()
      .then(setStudies)
      .catch(() => setError('Could not load worklist'));
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      Object.entries(jobsByStudyIdRef.current).forEach(([studyId, job]) => {
        if (TERMINAL_STATUSES.includes(job.status)) {
          return;
        }
        getSegmentationJobStatus(job.id).then((updated) => {
          setJobsByStudyId((prev) => ({ ...prev, [studyId]: updated }));
        });
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  function openInViewer(study) {
    const token = localStorage.getItem('access_token');
    const url = `${OHIF_BASE_URL}/viewer?StudyInstanceUIDs=${study.study_instance_uid}&token=${token}`;
    window.open(url, '_blank');
  }

  async function handleRunSegmentation(study) {
    try {
      const job = await runSegmentation(study.id);
      setJobsByStudyId((prev) => ({ ...prev, [study.id]: job }));
    } catch {
      setError('Could not start AI segmentation');
    }
  }

  function handleLogout() {
    logout();
    navigate('/login');
  }

  function openOhifStudyList() {
    const token = localStorage.getItem('access_token');
    window.open(`${OHIF_BASE_URL}/?token=${token}`, '_blank');
  }

  return (
    <div className="worklist-page">
      <header>
        <h1>Nurad</h1>
        <div>
          <button onClick={openOhifStudyList}>Open OHIF Study List</button>
          <button onClick={handleLogout}>Log out</button>
        </div>
      </header>
      {error && <p className="error">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Patient</th>
            <th>Patient ID</th>
            <th>Modality</th>
            <th>Study Date</th>
            <th>Description</th>
            <th></th>
            <th>AI Segmentation</th>
          </tr>
        </thead>
        <tbody>
          {studies.map((study) => {
            const job = jobsByStudyId[study.id];
            return (
              <tr key={study.id}>
                <td>{study.patient_name}</td>
                <td>{study.patient_id}</td>
                <td>{study.modalities}</td>
                <td>{study.study_date}</td>
                <td>{study.study_description}</td>
                <td>
                  <button onClick={() => openInViewer(study)}>Open</button>
                </td>
                <td>
                  {job ? (
                    <span className={`job-status job-status-${job.status.toLowerCase()}`}>
                      {job.status}
                    </span>
                  ) : (
                    <button onClick={() => handleRunSegmentation(study)}>
                      Run AI Segmentation
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
