export default function SchemaTable({ schema }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Field</th>
            <th>Key</th>
            <th>Data type</th>
            <th>Length</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {schema.fields.map((f, i) => (
            <tr key={i}>
              <td>{f.field_name}</td>
              <td>{f.key ? "✓" : ""}</td>
              <td>{f.data_type}</td>
              <td>{f.length}</td>
              <td className="muted">{f.notes || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
