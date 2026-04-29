import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler
from ai_agent import PawPalAgent
from rag import GuidelineRetriever

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("AI-powered pet care scheduler — powered by Gemini")

# ── Session state ──────────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_time=120)
if "result" not in st.session_state:
    st.session_state.result = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

owner = st.session_state.owner

# ── Owner ──────────────────────────────────────────────────────────────────────
st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Name", value=owner.name)
with col2:
    owner.update_availability(
        st.number_input("Available time (min)", min_value=0, max_value=480, value=owner.available_time)
    )

# ── Pets ───────────────────────────────────────────────────────────────────────
st.subheader("Pets")
with st.expander("Add a pet"):
    pet_name   = st.text_input("Pet name", key="pname")
    species    = st.selectbox("Species", ["dog", "cat", "other"], key="pspecies")
    age        = st.number_input("Age", min_value=0, max_value=30, value=2, key="page")
    care_needs = st.multiselect("Care needs", ["walk", "feed", "play", "groom", "meds"], key="pneeds")
    if st.button("Add pet"):
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age), care_needs=care_needs))
        st.session_state.result = None
        st.rerun()

for pet in owner.get_all_pets():
    st.write(pet.describe())

if not owner.get_all_pets():
    st.info("Add a pet to get started.")

# ── Tasks ──────────────────────────────────────────────────────────────────────
st.subheader("Tasks")
if owner.get_all_pets():
    with st.expander("Add a task"):
        pet_names = [p.name for p in owner.get_all_pets()]
        sel_pet_name = st.selectbox("Assign to", pet_names, key="tpet")
        sel_pet = next(p for p in owner.get_all_pets() if p.name == sel_pet_name)

        c1, c2, c3 = st.columns(3)
        with c1:
            title    = st.text_input("Title", value="Morning walk", key="ttitle")
        with c2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20, key="tdur")
        with c3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="tpri")

        c4, c5, c6 = st.columns(3)
        with c4:
            time_str  = st.text_input("Time (HH:MM)", value="09:00", key="ttime")
        with c5:
            category  = st.selectbox("Category", ["walk", "feed", "play", "groom", "meds", "general"], key="tcat")
        with c6:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], key="tfreq")

        desc = st.text_area("Description", value="Describe the task.", key="tdesc")

        if st.button("Add task"):
            sel_pet.add_task(Task(
                title=title, description=desc,
                duration_minutes=int(duration), time=time_str,
                priority=priority, category=category, frequency=frequency,
            ))
            st.session_state.result = None
            st.rerun()

    # Current task table
    rows = [
        {"Pet": p.name, "Task": t.title, "Time": t.time,
         "Duration": t.duration_minutes, "Priority": t.priority,
         "Status": "done" if t.is_complete else "pending"}
        for p in owner.get_all_pets() for t in p.get_tasks()
    ]
    if rows:
        st.table(rows)

st.divider()

# ── RAG: Suggested Tasks ───────────────────────────────────────────────────────
if owner.get_all_pets():
    st.subheader("Suggested Tasks")
    st.caption("Based on each pet's species and age — from care guidelines.")
    retriever = GuidelineRetriever()

    for pet in owner.get_all_pets():
        existing_categories = [t.category for t in pet.get_tasks()]
        suggestions = retriever.suggest(pet.species, pet.age, pet.care_needs, existing_categories)

        if suggestions:
            with st.expander(f"{pet.name} — {len(suggestions)} suggestion(s)"):
                for s_idx, g in enumerate(suggestions):
                    st.markdown(f"**{g['category'].capitalize()}** · {g['priority']} priority · {g['duration']}min · {g['frequency']}")
                    st.caption(g["text"])
                    if st.button("+ Add this task", key=f"rag_{pet.name}_{s_idx}"):
                        pet.add_task(Task(
                            title=g["category"].capitalize(),
                            description=g["text"],
                            duration_minutes=g["duration"],
                            priority=g["priority"],
                            category=g["category"],
                            frequency=g["frequency"],
                        ))
                        st.session_state.result = None
                        st.rerun()

st.divider()

# ── Run Agent ──────────────────────────────────────────────────────────────────
st.subheader("Run Agent")

if st.button("▶ Run Agent", type="primary", disabled=not owner.get_all_pets()):
    with st.spinner("Gemini is planning your day…"):
        agent = PawPalAgent(owner)
        st.session_state.result    = agent.run()
        st.session_state.scheduler = agent.scheduler

result = st.session_state.result

if result:
    # Guardrail warnings
    if result["issues"]:
        st.warning("Input issues found (logged):")
        for i in result["issues"]:
            st.write(f"- {i}")

    # Conflicts resolved
    if result["conflicts_resolved"]:
        st.info("Time conflicts were detected and resolved automatically:")
        for c in result["conflicts_resolved"]:
            st.write(f"- {c}")

    # ASCII graph
    st.markdown("### Daily Plan")
    st.code(result["graph"], language=None)

    # Gemini explanation
    st.markdown("**Gemini says:**")
    st.write(result["explanation"])

    # Summary
    st.success(result["summary"])

    # Mark tasks complete
    st.markdown("### Mark Tasks Done")
    plan_titles = {t.title for t in result["plan"]}
    scheduler   = st.session_state.scheduler
    any_shown   = False

    idx = 0
    for pet in owner.get_all_pets():
        for task in pet.pending_tasks():
            if task.title in plan_titles:
                any_shown = True
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"**{task.title}** ({pet.name}) — {task.time}, {task.duration_minutes}min [{task.priority}]")
                with c2:
                    if st.button("Done", key=f"done_{idx}"):
                        scheduler.complete_task(pet.name, task.title)
                        st.session_state.result = None
                        st.rerun()
                idx += 1

    if not any_shown:
        st.info("All planned tasks complete. Run the agent again to re-plan.")

    # Agent logs
    with st.expander("Agent logs"):
        for entry in result["logs"]:
            st.text(f"{entry['time']}  [{entry['step']}]  {entry['detail']}")
