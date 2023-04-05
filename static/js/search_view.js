$('.add-filter').on('click', function() {
    var add_condition = $(this).attr('class').split(' ')[0];
    var text = $(this).siblings().eq(0).text();

    if ($('.setting_filter_list').children().hasClass(add_condition)) {
        if (confirm('조건['+text+']을 변경하시겠습니까?')) {
            $('.'+add_condition+'.setting_filter').remove();
            var input_min = $('.'+add_condition+'_min').val();
            var input_max = $('.'+add_condition+'_max').val();

            if (input_min == '') {
                $('.'+add_condition+'_min').val('0');
            }
            if (input_max == '') {
                $('.'+add_condition+'_max').val('0');
            }
            if ( Number(input_min) < 0 && Number(input_max) < 0) {
                if (Number(input_min) > Number(input_max)) {
                    var set_filter = $('<span>', {
                        class: add_condition + ' setting_filter badge text-bg-primary mx-1',
                        text: text + ':' + input_min + '~' + input_max,
                        click: remove_filter
                    });
                    $('.setting_filter_list').append(set_filter);
                } else {
                    alert('올바른 범위의 숫자를 입력해 주십시오.');
                    $('.'+add_condition+'_min').val('');
                    $('.'+add_condition+'_max').val('');
                }
            } else { 
                if ((Number(input_max) > Number(input_min))) {
                    var set_filter = $('<span>', {
                        class: add_condition + ' setting_filter badge text-bg-primary mx-1',
                        text: text + ':' + input_min + '~' + input_max,
                        click: remove_filter
                    });
                    $('.setting_filter_list').append(set_filter);
                } else {
                    alert('올바른 범위의 숫자를 입력해 주십시오.');
                    $('.'+add_condition+'_min').val('');
                    $('.'+add_condition+'_max').val('');
                }
            }
        }
    } else {
        var input_min = $('.'+add_condition+'_min').val();
        var input_max = $('.'+add_condition+'_max').val();

        if (input_min == '') {
            $('.'+add_condition+'_min').val('0');
        }
        if (input_max == '') {
            $('.'+add_condition+'_max').val('0');
        }
        if ( Number(input_min) < 0 && Number(input_max) < 0) {
            if (Number(input_min) > Number(input_max)) {
                var set_filter = $('<span>', {
                    class: add_condition + ' setting_filter badge text-bg-primary mx-1',
                    text: text + ':' + input_min + '~' + input_max,
                    click: remove_filter
                });
                $('.setting_filter_list').append(set_filter);
            } else {
                alert('올바른 범위의 숫자를 입력해 주십시오.');
                $('.'+add_condition+'_min').val('');
                $('.'+add_condition+'_max').val('');
            }
        } else { 
            if ((Number(input_max) > Number(input_min))) {
                var set_filter = $('<span>', {
                    class: add_condition + ' setting_filter badge text-bg-primary mx-1',
                    text: text + ':' + input_min + '~' + input_max,
                    click: remove_filter
                });
                $('.setting_filter_list').append(set_filter);
            } else {
                alert('올바른 범위의 숫자를 입력해 주십시오.');
                $('.'+add_condition+'_min').val('');
                $('.'+add_condition+'_max').val('');
            }
        }
    }
});

function remove_filter() {
    var setting_condition = $(this).attr('class').split(' ')[0];
    $('.'+setting_condition+'.setting_filter').remove();
    $('input.'+setting_condition+'_min').val('');
    $('input.'+setting_condition+'_max').val('');
}

function remove_corp() {
    $("span[name='corp']").remove();
    $('#search_input').val('');
}

$('.filter_item').on('click', function() {
    var toggle_condition = $(this).attr('class').split(' ')[0];
    $('.input_data').hide();
    $('.'+toggle_condition+'_toggle').show();
    $('.submit').show();
});

$(function () {
    $('[data-toggle="tooltip"]').tooltip();

    $('[data-toggle="tooltip"]').on('click', function () {
        $(this).tooltip('hide');
    });
})

$('.year').on('click', function(e) {
    const target = e.target;
    const value = $(target).data('value');
    $('#year').val(value);
});

$('.quarter').on('click', function(e) {
    const target = e.target;
    const value = $(target).data('value');
    $('#quarter').val(value);
});