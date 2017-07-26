no_datepickers = 7

function selectDate(selected, i) {
    if (!selected) {
        return
    }
    var minDate = moment(selected, 'DD/MM/YYYY');
    minDate = minDate.add(1, "days");
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


$(document).ready(function() {
    selectDate(new Date(), 0);
    for (i = 1; i < no_datepickers+1; i++) {
        $.datepicker._clearDate($('#datepicker'+i));
    }
});


$('button[name="add_group"]').on('click', function(e) {
    var $form = $(this).closest('form');
    e.preventDefault();
    if ($('#datepicker1').val()) {
        $('#confirm').modal({
          backdrop: 'static',
          keyboard: false
        })
        .one('click', '#add', function(e) {
          $form.trigger('submit');
        });
    }
    else {
        $('#incomplete').modal({
          backdrop: 'static',
          keyboard: false
        })
    }

});