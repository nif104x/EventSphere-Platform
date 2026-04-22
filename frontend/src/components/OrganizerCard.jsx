const OrganizerCard = ({ organizer, selected, onToggleSelect }) => {
  const rating = organizer.avg_rating != null ? Number(organizer.avg_rating) : null;
  const count = organizer.review_count ?? 0;

  return (
    <label className={`org-card ${selected ? 'org-card--selected' : ''}`}>
      <input
        type="checkbox"
        className="org-card__input"
        checked={selected}
        onChange={onToggleSelect}
        aria-label={`Select ${organizer.company_name}`}
      />
      <div className="org-card__body">
        <h3>{organizer.company_name}</h3>
        <p className="muted">{organizer.primary_category}</p>
        <p className="org-card__email">{organizer.email}</p>
        <p className="org-card__meta">
          Verified: {String(organizer.is_verified)}
          {rating != null && !Number.isNaN(rating) && (
            <span className="org-card__rating" title={`${count} review(s)`}>
              {' '}
              · ★ {rating.toFixed(1)}
              {count > 0 ? ` (${count})` : ''}
            </span>
          )}
        </p>
      </div>
    </label>
  );
};

export default OrganizerCard;
