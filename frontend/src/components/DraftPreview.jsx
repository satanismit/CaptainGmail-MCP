import { useState } from 'react';
import { createDraft } from '../services/api';

function DraftPreview({ pendingAction, onConfirm, onCancel, showToast }) {
  const [isCreating, setIsCreating] = useState(false);

  if (!pendingAction || pendingAction.tool_name !== 'create_gmail_draft') {
    return null;
  }

  const { to, subject, body } = pendingAction.arguments || {};

  const handleCreate = async () => {
    setIsCreating(true);
    try {
      await createDraft(to, subject, body);
      showToast('Draft created successfully in Gmail.');
      onConfirm();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div style={{ padding: '0 24px 8px' }}>
      <div className="draft-preview">
        <div className="draft-preview__title">📝 Draft Preview</div>
        <div className="draft-preview__field">
          <div className="draft-preview__label">To</div>
          <div className="draft-preview__value">{to}</div>
        </div>
        <div className="draft-preview__field">
          <div className="draft-preview__label">Subject</div>
          <div className="draft-preview__value">{subject}</div>
        </div>
        <div className="draft-preview__field">
          <div className="draft-preview__label">Body</div>
          <div className="draft-preview__body">{body}</div>
        </div>
        <div className="draft-preview__actions">
          <button
            className="btn btn--primary"
            onClick={handleCreate}
            disabled={isCreating}
          >
            {isCreating ? 'Creating...' : '✅ Create Draft'}
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
