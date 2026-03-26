document.addEventListener('DOMContentLoaded', () => {
    const calendarEl = document.getElementById('calendar');
    const taskModal = document.getElementById('taskModal');
    const closeBtns = document.getElementById('closeModal');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: '',
            center: 'title',
            right: 'prev,next',
        },
        events: async (info) => {
            try {
                const response = await fetch(`/worker-schedule/get-worker-schedules/`);
                const tasksJson = await response.json();

                const tasksJsonAdjusted = tasksJson.map(event => {
                    if (event.end) {
                        let endDate = new Date(event.end);
                        endDate.setDate(endDate.getDate() + 1);
                        event.end = endDate.toISOString().split('T')[0];
                    }
                    return event;
                });

                return tasksJsonAdjusted;
            } catch (error) {
                console.error('Error fetching tasks:', error);
                return [];
            }
        },
        eventClick: (info) => {
            const { event } = info; 

            taskModal.style.display = 'flex';

            document.getElementById('eventModalTitle').textContent = event.title;
            document.getElementById('eventTaskName').value = event.title || '';
            document.getElementById('eventModalDescription').value = event.extendedProps.description || 'No description provided';
            document.getElementById('eventModalStart').value = event.start.toISOString().split('T')[0];
            document.getElementById('eventModalEnd').value = event.end ? event.end.toISOString().split('T')[0] : '';
            document.getElementById('progressFill').style.width = `${event.extendedProps.progress || 0}%`;
            document.getElementById('progressPercentage').textContent = `${event.extendedProps.progress || 0}%`;

            
            modal.style.display = 'flex';
        },
    });

    calendar.render();

    closeBtns.addEventListener('click', () => {
        if (taskModal) {
            taskModal.style.display = 'none';
        }
    });

    window.onclick = function(event) {
        if (event.target === taskModal) {
            taskModal.style.display = 'none';
        }
    };

});


