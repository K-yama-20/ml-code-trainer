import type { SqlProblem, SqlResultTable } from "../types/domain";

export function SqlTable({
  table,
  label,
  descriptions,
}: {
  table: SqlResultTable;
  label: string;
  descriptions?: string[];
}) {
  return (
    <div
      className="sql-table-scroll"
      role="region"
      aria-label={label}
      tabIndex={0}
    >
      <table className="sql-table" aria-label={label}>
        <thead>
          <tr>
            {table.columns.map((column, i) => (
              <th scope="col" key={i}>
                {column}
                {descriptions?.[i] && <small>{descriptions[i]}</small>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.length ? (
            table.rows.map((row, i) => (
              <tr key={i}>
                {row.map((value, j) => (
                  <td
                    key={j}
                    className={
                      value === null || value === ""
                        ? "sql-empty-cell"
                        : undefined
                    }
                  >
                    {value === null ? "NULL" : value === "" ? "''" : value}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={table.columns.length}>0行</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function SqlSamples({
  sql,
  openFirst = true,
  caseIndex = 0,
}: {
  sql: SqlProblem;
  openFirst?: boolean;
  caseIndex?: number;
}) {
  return (
    <div className="sql-samples" aria-label="サンプルデータ">
      {sql.tables.map((table, i) => (
        <details key={table.name} open={openFirst && i === 0}>
          <summary>
            <code>{table.name}</code> · {table.description}
          </summary>
          <SqlTable
            label={`${table.name} のサンプル`}
            table={{
              columns: table.columns.map(({ name }) => name),
              rows: sql.cases[caseIndex].rows[i],
            }}
            descriptions={table.columns.map(({ description }) => description)}
          />
        </details>
      ))}
    </div>
  );
}

export function sqlTable(value: unknown): SqlResultTable | undefined {
  const table = value as Partial<SqlResultTable> | null;
  if (
    table &&
    Array.isArray(table.columns) &&
    table.columns.every((name) => typeof name === "string") &&
    Array.isArray(table.rows) &&
    table.rows.every(
      (row) =>
        Array.isArray(row) &&
        row.every(
          (cell) =>
            cell === null ||
            typeof cell === "number" ||
            typeof cell === "string",
        ),
    )
  ) {
    return table as SqlResultTable;
  }
}
