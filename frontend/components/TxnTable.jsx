"use client";
import { Table, Row, Btn, Badge } from "@/components/ui";
import { viewPdf } from "@/lib/api";

export default function TxnTable({ rows, showLearner, onRefund, empty }) {
  const head = ["Ref", "Date"];
  if (showLearner) head.push("Learner");
  head.push("Course", "Method", "Amount", "Status", "");
  async function receipt(t) {
    try { await viewPdf("/txns/" + t.id + "/receipt"); }
    catch (e) { alert(e.message); }
  }
  return (
    <Table head={head} empty={empty || "No payments recorded yet."}>
      {rows.map((t) => (
        <Row key={t.id}>
          <td style={{ fontFamily: "ui-monospace,monospace", fontSize: 12 }}>{t.ref}</td>
          <td>{t.date}</td>
          {showLearner && <td>{t.learner}</td>}
          <td>{t.course}</td>
          <td>{t.method} •••• {t.card_last4}</td>
          <td>{"\u09f3"}{t.amount}</td>
          <td><Badge st={t.status} /></td>
          <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
            {t.status === "success" && <Btn tone="ghost" onClick={() => receipt(t)}>Receipt</Btn>}
            {t.status === "success" && onRefund && (
              <Btn tone="red" onClick={() => onRefund(t)} style={{ marginLeft: 6 }}>Refund</Btn>)}
          </td>
        </Row>
      ))}
    </Table>
  );
}