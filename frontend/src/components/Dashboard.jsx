import { useEffect } from 'react';
import {
  AlertTriangle,
  Mail,
  CheckSquare,
  Calendar,
  MessageSquare,
  ArrowRight,
  RefreshCw,
  FileEdit,
  Clock,
  Inbox,
  Star,
} from 'lucide-react';

function PriorityBadge({ priority }) {
  const p = (priority || 'Medium').toLowerCase();
  const colors = {
    high: { bg: '#FCEAEA', color: '#D93025', label: 'High' },
    medium: { bg: '#FEF7E0', color: '#E37400', label: 'Medium' },
    low: { bg: '#E6F4EA', color: '#188038', label: 'Low' },
  };
  const style = colors[p] || colors.medium;
  return (
    <span
      className="dashboard-priority-badge"
      style={{ background: style.bg, color: style.color }}
    >
      {style.label}
    </span>
  );
}

function SummaryCards({ summary }) {
  const cards = [
    {
      label: 'Important Emails',
      count: summary?.important_emails ?? 0,
      icon: <Star size={20} />,
      color: 'var(--google-red)',
      bg: '#FFF0EE',
    },
    {
      label: 'Pending Actions',
      count: summary?.pending_actions ?? 0,
      icon: <CheckSquare size={20} />,
      color: 'var(--google-blue)',
      bg: '#E8F0FE',
    },
    {
      label: 'Upcoming Deadlines',
      count: summary?.upcoming_deadlines ?? 0,
      icon: <Calendar size={20} />,
      color: 'var(--google-yellow)',
      bg: '#FEF7E0',
    },
    {
      label: 'Awaiting Replies',
      count: summary?.awaiting_replies ?? 0,
      icon: <MessageSquare size={20} />,
      color: 'var(--google-green)',
      bg: '#E6F4EA',
    },
  ];

  return (
    <div className="dashboard-summary">
      {cards.map((card) => (
        <div
          className="dashboard-summary-card"
          key={card.label}
          style={{ borderLeftColor: card.color }}
        >
          <div className="dashboard-summary-card__icon" style={{ background: card.bg, color: card.color }}>
            {card.icon}
          </div>
          <div className="dashboard-summary-card__info">
            <div className="dashboard-summary-card__count">{card.count}</div>
            <div className="dashboard-summary-card__label">{card.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function SectionHeader({ icon, title, count }) {
  return (
    <div className="dashboard-section__header">
      <span className="dashboard-section__icon">{icon}</span>
      <h3 className="dashboard-section__title">{title}</h3>
      {count !== undefined && (
        <span className="dashboard-section__count">{count}</span>
      )}
    </div>
  );
}

function EmptySection({ message }) {
  return (
    <div className="dashboard-section__empty">
      <Inbox size={20} />
      <span>{message}</span>
    </div>
  );
}

function ImportantEmailCard({ email, onOpenEmail }) {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card__header">
        <div className="dashboard-card__subject">{email.subject}</div>
        <PriorityBadge priority={email.priority} />
      </div>
      <div className="dashboard-card__meta">
        <span className="dashboard-card__sender">{email.sender_name || email.sender}</span>
        <span className="dashboard-card__date">{email.date}</span>
      </div>
      <div className="dashboard-card__reason">{email.reason}</div>
      {email.snippet && (
        <div className="dashboard-card__snippet">{email.snippet}</div>
      )}
      <div className="dashboard-card__actions">
        <button
          className="btn btn--secondary btn--small"
          onClick={() => onOpenEmail(email.message_id, email.subject)}
        >
          <Mail size={14} /> Open Email
        </button>
      </div>
    </div>
  );
}

function ActionItemCard({ item, onOpenEmail }) {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card__header">
        <div className="dashboard-card__subject">{item.task}</div>
        <PriorityBadge priority={item.priority} />
      </div>
      <div className="dashboard-card__meta">
        <span className="dashboard-card__sender">Source: {item.source_subject}</span>
        {item.deadline && (
          <span className="dashboard-card__date">
            <Clock size={12} /> {item.deadline}
          </span>
        )}
      </div>
      <div className="dashboard-card__status">
        Status: <strong>{item.status || 'Pending'}</strong>
      </div>
      {item.source_message_id && (
        <div className="dashboard-card__actions">
          <button
            className="btn btn--secondary btn--small"
            onClick={() => onOpenEmail(item.source_message_id, item.source_subject)}
          >
            <Mail size={14} /> Open Source
          </button>
        </div>
      )}
    </div>
  );
}

function DeadlineCard({ item, onOpenEmail }) {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card__header">
        <div className="dashboard-card__subject">{item.task}</div>
        <span
          className="dashboard-priority-badge"
          style={{
            background: item.status === 'Overdue' ? '#FCEAEA' : '#FEF7E0',
            color: item.status === 'Overdue' ? '#D93025' : '#E37400',
          }}
        >
          {item.status || 'Upcoming'}
        </span>
      </div>
      <div className="dashboard-card__meta">
        <span className="dashboard-card__sender">Source: {item.source_subject}</span>
        <span className="dashboard-card__date">
          <Calendar size={12} /> {item.deadline}
        </span>
      </div>
      {item.source_message_id && (
        <div className="dashboard-card__actions">
          <button
            className="btn btn--secondary btn--small"
            onClick={() => onOpenEmail(item.source_message_id, item.source_subject)}
          >
            <Mail size={14} /> Open Source
          </button>
        </div>
      )}
    </div>
  );
}

function AwaitingReplyCard({ item, onOpenEmail, onDraftFollowUp }) {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card__header">
        <div className="dashboard-card__subject">{item.subject}</div>
      </div>
      <div className="dashboard-card__meta">
        <span className="dashboard-card__sender">{item.sender_name || item.sender}</span>
        <span className="dashboard-card__date">{item.last_date}</span>
      </div>
      <div className="dashboard-card__reason">{item.reason}</div>
      <div className="dashboard-card__actions">
        <button
          className="btn btn--secondary btn--small"
          onClick={() => onOpenEmail(item.thread_id, item.subject)}
        >
          <Mail size={14} /> Open Thread
        </button>
        <button
          className="btn btn--primary btn--small"
          onClick={() => onDraftFollowUp(item.subject, item.sender)}
        >
          <FileEdit size={14} /> Draft Reply
        </button>
      </div>
    </div>
  );
}

function FollowUpCard({ item, onOpenEmail, onDraftFollowUp }) {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card__header">
        <div className="dashboard-card__subject">{item.subject}</div>
      </div>
      <div className="dashboard-card__meta">
        <span className="dashboard-card__sender">{item.sender_name || item.sender}</span>
      </div>
      <div className="dashboard-card__reason">{item.reason}</div>
      {item.suggested_action && (
        <div className="dashboard-card__action-hint">
          <ArrowRight size={14} /> {item.suggested_action}
        </div>
      )}
      <div className="dashboard-card__actions">
        <button
          className="btn btn--secondary btn--small"
          onClick={() => onOpenEmail(item.thread_id, item.subject)}
        >
          <Mail size={14} /> Open Thread
        </button>
        <button
          className="btn btn--primary btn--small"
          onClick={() => onDraftFollowUp(item.subject, item.sender)}
        >
          <FileEdit size={14} /> Draft Follow-up
        </button>
      </div>
    </div>
  );
}

function Dashboard({ dashboardData, isLoading, error, onRefresh, onOpenEmail, onDraftFollowUp }) {
  useEffect(() => {
    if (!dashboardData && !isLoading && !error) {
      onRefresh();
    }
  }, [dashboardData, isLoading, error, onRefresh]);

  if (isLoading && !dashboardData) {
    return (
      <div className="dashboard">
        <div className="dashboard-loading">
          <RefreshCw size={32} className="dashboard-loading__spinner" />
          <p>Analyzing your inbox with AI...</p>
          <p className="dashboard-loading__sub">This may take a moment</p>
        </div>
      </div>
    );
  }

  if (error && !dashboardData) {
    return (
      <div className="dashboard">
        <div className="dashboard-error">
          <AlertTriangle size={32} />
          <p>{error}</p>
          <button className="btn btn--primary" onClick={onRefresh}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) return null;

  const {
    summary,
    important_emails = summary?.important_emails_list || [],
    pending_actions = summary?.pending_actions_list || [],
    upcoming_deadlines = summary?.upcoming_deadlines_list || [],
    awaiting_replies = summary?.awaiting_replies_list || [],
    follow_up_recommendations = summary?.follow_up_recommendations || [],
    retrieved_at,
    warnings = [],
  } = dashboardData;

  return (
    <div className="dashboard">
      <div className="dashboard-top">
        <div className="dashboard-top__left">
          <h2 className="dashboard-top__title">AI Priority Inbox</h2>
          {retrieved_at && (
            <span className="dashboard-top__time">
              Updated {new Date(retrieved_at).toLocaleTimeString()}
            </span>
          )}
        </div>
        <button
          className="btn btn--secondary btn--small"
          onClick={onRefresh}
          disabled={isLoading}
        >
          <RefreshCw size={14} className={isLoading ? 'dashboard-loading__spinner' : ''} />
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {warnings.length > 0 && (
        <div className="dashboard-warnings">
          {warnings.map((w, i) => (
            <div key={i} className="dashboard-warning">
              <AlertTriangle size={14} /> {w}
            </div>
          ))}
        </div>
      )}

      <SummaryCards summary={summary} />

      {/* Important Emails */}
      <div className="dashboard-section">
        <SectionHeader
          icon={<Star size={18} color="var(--google-red)" />}
          title="Important Emails"
          count={important_emails.length}
        />
        {important_emails.length === 0 ? (
          <EmptySection message="No emails flagged as important" />
        ) : (
          <div className="dashboard-section__cards">
            {important_emails.map((email, i) => (
              <ImportantEmailCard key={email.message_id || i} email={email} onOpenEmail={onOpenEmail} />
            ))}
          </div>
        )}
      </div>

      {/* Pending Actions */}
      <div className="dashboard-section">
        <SectionHeader
          icon={<CheckSquare size={18} color="var(--google-blue)" />}
          title="Pending Actions"
          count={pending_actions.length}
        />
        {pending_actions.length === 0 ? (
          <EmptySection message="No pending action items found" />
        ) : (
          <div className="dashboard-section__cards">
            {pending_actions.map((item, i) => (
              <ActionItemCard key={item.source_message_id || i} item={item} onOpenEmail={onOpenEmail} />
            ))}
          </div>
        )}
      </div>

      {/* Upcoming Deadlines */}
      <div className="dashboard-section">
        <SectionHeader
          icon={<Calendar size={18} color="var(--google-yellow)" />}
          title="Upcoming Deadlines"
          count={upcoming_deadlines.length}
        />
        {upcoming_deadlines.length === 0 ? (
          <EmptySection message="No upcoming deadlines detected" />
        ) : (
          <div className="dashboard-section__cards">
            {upcoming_deadlines.map((item, i) => (
              <DeadlineCard key={item.source_message_id || i} item={item} onOpenEmail={onOpenEmail} />
            ))}
          </div>
        )}
      </div>

      {/* Awaiting Replies */}
      <div className="dashboard-section">
        <SectionHeader
          icon={<MessageSquare size={18} color="var(--google-green)" />}
          title="Awaiting Replies"
          count={awaiting_replies.length}
        />
        {awaiting_replies.length === 0 ? (
          <EmptySection message="No conversations awaiting your reply" />
        ) : (
          <div className="dashboard-section__cards">
            {awaiting_replies.map((item, i) => (
              <AwaitingReplyCard
                key={item.thread_id || i}
                item={item}
                onOpenEmail={onOpenEmail}
                onDraftFollowUp={onDraftFollowUp}
              />
            ))}
          </div>
        )}
      </div>

      {/* Follow-up Recommendations */}
      <div className="dashboard-section">
        <SectionHeader
          icon={<ArrowRight size={18} color="var(--google-blue)" />}
          title="Recommended Follow-ups"
          count={follow_up_recommendations.length}
        />
        {follow_up_recommendations.length === 0 ? (
          <EmptySection message="No follow-up recommendations" />
        ) : (
          <div className="dashboard-section__cards">
            {follow_up_recommendations.map((item, i) => (
              <FollowUpCard
                key={item.thread_id || i}
                item={item}
                onOpenEmail={onOpenEmail}
                onDraftFollowUp={onDraftFollowUp}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
