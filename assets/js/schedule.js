const scheduleStatus = document.querySelector("#schedule-status");
const list = document.querySelector("#schedule-events");
const team = document.querySelector("#schedule-team");
const dayFormat = new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" });
const timeFormat = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", timeStyle: "short" });
const headingFormat = new Intl.DateTimeFormat("en-US", { timeZone: "UTC", dateStyle: "medium" });
const dayMs = 86400000;

function dayKey(date) {
    const parts = Object.fromEntries(dayFormat.formatToParts(date).map(({type, value}) => [type, value]));
    return Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day));
}

async function showSchedule() {
    const response = await fetch("schedule.json");
    if (!response.ok) throw new Error("Schedule unavailable");
    const data = await response.json();
    if (!data.configured) return;
    const events = data.events.map(event => {
        const timed = event.start.includes("T");
        const start = new Date(event.start);
        return { ...event, day: timed ? dayKey(start) : +start, time: timed ? timeFormat.format(start) : "All day" };
    });
    for (const name of [...new Set(events.flatMap(event => event.teams))].sort()) {
        team.add(new Option(name, name));
    }
    const today = new Date(dayKey(new Date()));
    let week = +today - today.getUTCDay() * dayMs;
    function render() {
        const visible = events.filter(event => event.day >= week && event.day < week + 7 * dayMs &&
            (!team.value || event.teams.includes(team.value)));
        list.replaceChildren();
        for (const event of visible) {
            const item = document.createElement("li");
            const where = event.location ? ` · ${event.location}` : "";
            item.textContent = `${headingFormat.format(event.day)} · ${event.time} · ${event.cancelled ? "Cancelled: " : ""}${event.title} · ${event.teams.join(", ")}${where}`;
            list.append(item);
        }
        scheduleStatus.textContent = `Week of ${headingFormat.format(week)} · ${visible.length ? visible.length + " event(s)" : "No events scheduled"}`;
    }
    document.querySelector("#schedule-previous").addEventListener("click", () => { week -= 7 * dayMs; render(); });
    document.querySelector("#schedule-next").addEventListener("click", () => { week += 7 * dayMs; render(); });
    team.addEventListener("change", render);
    document.querySelector("#schedule-controls").hidden = false;
    document.querySelector("#schedule-subscribe").hidden = false;
    render();
}

showSchedule().catch(() => { scheduleStatus.textContent = "The league schedule is unavailable. Check GameChanger for team updates."; });
