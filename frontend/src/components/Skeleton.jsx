/** Placeholder shown while a profile loads for the first time. */
export default function Skeleton() {
  return (
    <>
      <section className="card">
        <div className="sk-header">
          <div className="skeleton sk-avatar" />
          <div className="sk-lines">
            <div className="skeleton sk-line" style={{ width: "40%", height: 22 }} />
            <div className="skeleton sk-line" style={{ width: "25%" }} />
            <div className="skeleton sk-line" style={{ width: "60%" }} />
          </div>
        </div>
      </section>
      <section className="card"><div className="skeleton sk-block" /></section>
      <section className="card"><div className="skeleton sk-block" style={{ height: 120 }} /></section>
    </>
  );
}
