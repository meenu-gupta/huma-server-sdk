sources_to_load_cnt = 1

function data_req (url, callback) {
    req = new XMLHttpRequest()
    req.addEventListener('load', callback)
    req.open('GET', url)
    req.setRequestHeader('Cache-Control', 'no-cache');
    req.send()
}

function add_recur_events() {
    if (sources_to_load_cnt < 1) {
        $('#calendar').fullCalendar('addEventSource', expand_recur_events)
    } else {
        setTimeout(add_recur_events, 30)
    }
}

function load_ics(ics){
    data_req(ics.url, function(){
        let events = fc_events(this.response, ics.event_properties)
        events.forEach(el => {
            el.initialEndDate = el.end
            el.end = el.start
        })
        $('#calendar').fullCalendar('addEventSource', events)
        $("#refresh-button").prop("disabled", false)
    })
}

function refresh() {
    $("#calendar").fullCalendar("destroy")
    $("#refresh-button").prop("disabled", true)
    let userId = $("#user_id").val();
    let timezone = $("#timezone").val();
    // for later url_for("calendar_route.export_calendar")
    let url = `${window.location.protocol}//${window.location.host}/api/calendar/v1beta/user/${userId}/export?timezone=${timezone}&debug=true`
    startCalendar(url)
}

function startCalendar(url) {
    $('#calendar').fullCalendar({
        timezone: 'UTC',
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        defaultView: 'month',
        defaultDate: moment().format("YYYY-MM-DD"),
        eventClick: function(arg) {
            let msg = "Event title: " + arg.title + "\n\nStart Date: " + arg.start._d + "\n\nEnd Date: " + arg.initialEndDate + '\n\nExtraData: \n' + arg.description
            alert(msg)
            // alert(arg.title + "\n" +arg.start._d); // use *UTC* methods on the native Date Object
            // will output something like 'Sat, 01 Sep 2018 00:00:00 GMT'
        }
    })
    load_ics({url})
    add_recur_events()
}

function setUserData(data, fields) {
    let selected = $("#user_id").val();
    let obj = data.find(o => o.id === selected);
    if (obj) {
        Object.keys(fields).forEach(key => {
            document.getElementById(key + "Message").innerHTML = obj[key] || "No Data";
        })
    }
}
