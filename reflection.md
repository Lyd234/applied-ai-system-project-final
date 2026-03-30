# PawPal+ Project Reflection

## 1. System Design
Add pet information 
set daily schedule 
ablity to add/change the schedule
**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
I chose four classes owner, pet, task and daily plan. 
The owner can set availanlitu , preferance an st a schedule.
Pet holds the pet information and care needs, and includes methods to add tasks needed for the pet
Task class sets the duration and priority needed for the task
Dailyplan collects and schedules task for a day, add and removes task

**b. Design changes**

- Did your design change during implementation?
yes
- If yes, describe at least one change and why you made it.
There was a get health summary method added by claude which i removed , because it is out of scope for this app and a pet's health can only accurartely be determined by a vet.
I also removed is valid task method from pet class. It seemed redundent as the user can remove a daily plan using the method under daily plan.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
