const scheduleStatus = document.querySelector("#schedule-status");
const list = document.querySelector("#schedule-events");
const team = document.querySelector("#schedule-team");
const dayFormat = new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" });
const timeFormat = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", timeStyle: "short" });
const headingFormat = new Intl.DateTimeFormat("en-US", { timeZone: "UTC", dateStyle: "medium" });
const weekdayFormat = new Intl.DateTimeFormat("en-US", {
    weekday: "short", month: "short", day: "numeric", timeZone: "UTC"
});
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
        return { ...event, timestamp: +start, day: timed ? dayKey(start) : +start, time: timed ? timeFormat.format(start) : "All day" };
    });
    const names = data.teams ?? [...new Set(events.flatMap(event => event.teams))];
    for (const name of [...names].sort()) {
        team.add(new Option(name, name));
    }
    const today = new Date(dayKey(new Date()));
    let week = +today - today.getUTCDay() * dayMs;
    function render() {
        const visible = events.filter(event => event.day >= week && event.day < week + 7 * dayMs &&
            (!team.value || event.teams.includes(team.value)));
        visible.sort((a, b) => a.day - b.day || a.timestamp - b.timestamp || a.title.localeCompare(b.title));
        list.replaceChildren();
        for (let offset = 0; offset < 7; offset++) {
            const date = week + offset * dayMs;
            const column = document.createElement("section");
            column.className = "schedule-day";
            const heading = document.createElement("h3");
            heading.textContent = weekdayFormat.format(date);
            column.append(heading);
            const dayEvents = visible.filter(event => event.day === date);
            column.classList.toggle("schedule-day-empty", dayEvents.length === 0);
            for (const event of dayEvents) {
                const card = document.createElement("details");
                card.className = "schedule-event";
                const summary = document.createElement("summary");
                const time = document.createElement("span");
                time.className = "schedule-event-time";
                time.textContent = event.time;
                const title = document.createElement("span");
                title.textContent = (event.cancelled ? "Cancelled · " : "") + event.title;
                summary.append(time, title);
                card.append(summary);
                const details = document.createElement("div");
                details.className = "schedule-event-details";
                for (const [label, value] of [
                    ["Team", event.teams.join(", ")], ["Location", event.location], ["Notes", event.notes]
                ]) {
                    if (!value) continue;
                    const line = document.createElement("p");
                    const name = document.createElement("strong");
                    name.textContent = label;
                    line.append(name, document.createTextNode(value));
                    details.append(line);
                }
                card.append(details);
                column.append(card);
            }
            list.append(column);
        }
        scheduleStatus.textContent = `Week of ${headingFormat.format(week)} · ${visible.length ? visible.length + (visible.length === 1 ? " event" : " events") : "No events scheduled"}`;
        list.classList.toggle("schedule-week-empty", visible.length === 0);
    }
    document.querySelector("#schedule-previous").addEventListener("click", () => { week -= 7 * dayMs; render(); });
    document.querySelector("#schedule-next").addEventListener("click", () => { week += 7 * dayMs; render(); });
    team.addEventListener("change", render);
    document.querySelector("#schedule-controls").hidden = false;
    document.querySelector("#schedule-subscribe").hidden = false;
    render();
}

showSchedule().catch(() => { scheduleStatus.textContent = "The league schedule is unavailable. Check GameChanger for team updates."; });
