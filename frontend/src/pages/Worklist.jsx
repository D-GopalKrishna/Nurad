import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchWorklist, logout } from '../api';

const OHIF_BASE_URL = import.meta.env.VITE_OHIF_BASE_URL || 'http://localhost:3030';

export default function Worklist() {
  const [studies, setStudies] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchWorklist()
      .then(setStudies)
      .catch(() => setError('Could not load worklist'));
  }, []);

  function openInViewer(study) {
    const token = localStorage.getItem('access_token');
    const url = `${OHIF_BASE_URL}/viewer?StudyInstanceUIDs=${study.study_instance_uid}&token=${token}`;
    window.open(url, '_blank');
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
        <h1>Worklist</h1>
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
          </tr>
        </thead>
        <tbody>
          {studies.map((study) => (
            <tr key={study.id}>
              <td>{study.patient_name}</td>
              <td>{study.patient_id}</td>
              <td>{study.modalities}</td>
              <td>{study.study_date}</td>
              <td>{study.study_description}</td>
              <td>
                <button onClick={() => openInViewer(study)}>Open</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
