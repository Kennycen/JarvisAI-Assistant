const StatusIndicator = ({ status }) => {
  const getStatusColor = () => {
    if (status.includes("Connected")) return "#48bb78";
    if (status.includes("Error")) return "#f56565";
    if (status.includes("Connecting") || status.includes("Creating"))
      return "#ed8936";
    return "#718096";
  };

  return (
    <div className="status-indicator">
      <div
        className="status-dot"
        style={{ backgroundColor: getStatusColor() }}
      />
      <span className="status-text">{status}</span>
    </div>
  );
};

export default StatusIndicator;
