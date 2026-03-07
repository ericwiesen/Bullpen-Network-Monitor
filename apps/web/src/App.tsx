import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Watchlists from "./app/watchlists/Watchlists";
import WatchlistDetail from "./app/watchlists/WatchlistDetail";
import Entities from "./app/entities/Entities";
import Runs from "./app/results/Runs";
import RunDetail from "./app/results/RunDetail";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <nav className="nav">
        <Link to="/">Home</Link>
        <Link to="/watchlists">Watchlists</Link>
        <Link to="/entities">Entities</Link>
        <Link to="/runs">Runs</Link>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/watchlists" element={<Watchlists />} />
          <Route path="/watchlists/:id" element={<WatchlistDetail />} />
          <Route path="/entities" element={<Entities />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/runs/:id" element={<RunDetail />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

function Home() {
  return (
    <div>
      <h1>Monitoring Service</h1>
      <p>Create <strong>Entities</strong> (companies/people), add them to <strong>Watchlists</strong>, then start <strong>Runs</strong> to collect recent news and press. View results under Runs.</p>
    </div>
  );
}

export default App;
