"use client";

type Props = {
  title: string;
  description: string;
  children: React.ReactNode;
};

export default function TaskCard({ title, description, children }: Props) {
  return (
    <article className="card">
      <h3 className="text-xl font-semibold">{title}</h3>
      <p className="text-sm text-slate-600 mb-4">{description}</p>
      {children}
    </article>
  );
}
