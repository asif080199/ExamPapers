function view(url){
    document.sidebar.action=url;
}

function selectAll(id){
    var type = id.replace('selectAll', '').toLowerCase().slice(0,-1);
    var status = document.getElementById(id).checked;
    var checkboxes = new Array();
    checkboxes = document.getElementsByName(type);
    for (var i=0; i<checkboxes.length; i++)  {
        if (checkboxes[i].type == 'checkbox')   {
            checkboxes[i].checked = status;
            checkboxes[i].disabled = status;
        }
    }
}

function toggleAns(qid, button_id) {
    var ele_name = "sol_" + qid;
    var ele = document.getElementById(ele_name);
    var text = document.getElementById(button_id);
    if(ele.style.display == "block") {
            ele.style.display = "none";
        text.value = "View Solution";
    }
    else {
        ele.style.display = "block";
        text.value = "Hide Solution";
    }
}