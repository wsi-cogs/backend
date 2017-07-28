function selectDate(selected, i, add_days=1) {
    if (!selected) {
        return
    }
    var minDate = moment(selected, 'DD/MM/YYYY');
    minDate = minDate.add(add_days, "days");
    var nextPicker = $('#datepicker'+(i+1));
    nextPicker.datepicker("option", "minDate", minDate.toDate());
    if (!nextPicker.val()) {
        nextPicker.datepicker("setDate", minDate.toDate());
    }
    if (i <= no_datepickers) {
        selectDate(nextPicker.val(), i+1);
    }
}


for (i = 1; i < no_datepickers+1; i++) {
    $(function(i) {
        return function() {
            $('#datepicker'+i).datepicker({
                dateFormat: 'dd/mm/yy',
                onSelect: function(selected) {selectDate(selected, i)}
            });
        }
    }(i));
}


