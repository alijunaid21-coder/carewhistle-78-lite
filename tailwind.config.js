module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        base: { bg: "#f7f8fb", card: "#ffffff", ink: "#111827", muted: "#6b7280" },
        neon: { blue: "#3b82f6", green: "#22c55e", pink: "#ec4899", purple: "#8b5cf6", amber: "#f59e0b", cyan: "#06b6d4" }
      },
      boxShadow: {
        glass: "0 10px 30px rgba(31,41,55,.08), inset 0 1px 0 rgba(255,255,255,.5)"
      }
    }
  },
  plugins: [],
}
