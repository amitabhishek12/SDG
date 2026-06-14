export default function Stepper({ steps, current }) {
  return (
    <ol className="stepper">
      {steps.map((label, i) => (
        <li
          key={label}
          className={
            i === current ? "active" : i < current ? "done" : "upcoming"
          }
        >
          <span className="dot">{i < current ? "✓" : i + 1}</span>
          <span className="label">{label}</span>
        </li>
      ))}
    </ol>
  );
}
