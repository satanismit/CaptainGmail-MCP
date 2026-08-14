const TEMPLATES = {
  'Professional new message':
    'Write a professional email to [recipient name or email] with subject "[subject line]" about ' +
    '[short purpose]. Keep it ~150\u2013200 words, polite, include a brief call to action, and sign as ' +
    '"[Your Name]". Don\u2019t send \u2014 prepare a draft.',

  'Reply to message (by ID)':
    'Reply to the email with message ID [MESSAGE_ID]. Say thanks, answer the question about [topic], ' +
    'include these points: [point 1; point 2], and end with a friendly sign-off. Create a Gmail draft only.',

  'Follow-up':
    'Draft a short follow\u2011up to [recipient or thread subject] asking for a status update. Reference earlier ' +
    'email dated [date] and be polite. Keep it under 80 words and offer next steps.',

  'Summarize thread into reply':
    'Summarize the recent thread about "[topic]" and draft a response that: 1) acknowledges received info, ' +
    '2) lists two action items, 3) asks one clarifying question. Make it concise and professional.',

  'Meeting / schedule request':
    'Draft an email to [recipient] proposing a meeting on [two date/time options] for [purpose]. Include duration ' +
    '(30 mins), a proposed agenda, and ask them to confirm or propose alternatives.',

  'Casual short':
    'Write a short, casual note to [recipient] asking about [topic]. Keep it under 50 words and friendly.',

  'Return JSON draft (tool)':
    'Prepare a Gmail draft only. Return a JSON object with keys `to`, `subject`, and `body`. `to`: [email], ' +
    '`subject`: short descriptive subject, `body`: full email text (include signature "[Your Name]"). Do not send.',
};

export default TEMPLATES;
