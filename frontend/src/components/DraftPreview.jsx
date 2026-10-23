import { useState } from 'react';
import { FileEdit, Check } from 'lucide-react';
import { createDraft } from '../services/api';

function DraftPreview({ pendingAction, onConfirm, onCancel, showToast }) {
  const [isCreating, setIsCreating] = useState(false);
  const [draft, setDraft] = useState(null);

  if (!pendingAction || pendingAction.tool_name !== 'create_gmail_draft') {
    return null;
  }

  const { to, subject, body } = pendingAction.arguments || {};
  const currentDraft = draft || { to: to || '', subject: subject || '', body: body || '' };

  const updateDraft = (field, value) => {
    setDraft((previous) => ({
      ...(previous || currentDraft),
      [field]: value,
    }));
  };

  const handleCreate = async () => {
    setIsCreating(true);
    try {
      await createDraft(currentDraft.to, currentDraft.subject, currentDraft.body);
      showToast('Draft created successfully in Gmail.');
      onConfirm();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="draft-preview-wrapper">
      <div className="draft-preview">
        <div className="draft-preview__title">
          <FileEdit /> Draft Preview
        </div>
        <div className="draft-preview__field">
          <div className="draft-preview__label">To</div>
          <input className="draft-preview__value" value={currentDraft.to} onChange={(e) => updateDraft('to', e.target.value)} aria-label="Draft recipient" />
        </div>
        <div className="draft-preview__field">
          <div className="draft-preview__label">Subject</div>
          <input className="draft-preview__value" value={currentDraft.subject} onChange={(e) => updateDraft('subject', e.target.value)} aria-label="Draft subject" />
        </div>
        <div className="draft-preview__field">
          <div className="draft-preview__label">Body</div>
          <textarea className="draft-preview__body" value={currentDraft.body} onChange={(e) => updateDraft('body', e.target.value)} aria-label="Draft body" />
        </div>
        <div className="draft-preview__actions">
          <button
            className="btn btn--success"
            onClick={handleCreate}
            disabled={isCreating}
          >
            <Check />
            {isCreating ? 'Creating...' : 'Create Draft'}
          </button>
          <button
            className="btn btn--danger"
            onClick={onCancel}
            disabled={isCreating}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default DraftPreview;
