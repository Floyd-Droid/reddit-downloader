$(document).ready(function () {
  let dTable = $("table.table").DataTable({
    columnDefs: [{
      // Allow selection of rows
      orderable: false,
      className: 'select-checkbox',
      targets: 0
    }, {
      // Center cell data
      className: 'dt-center',
      targets: '_all'
    },
    {
      // Hide the column with the id.
      targets: [-1],
      visible: false,
      searchable: false
    }],
    select: {
      style: 'os',
      selector: 'td:first-child'
    },
    dom: 'lBfrtip',
    buttons: [
      'selectAll',
      'selectNone'
    ],
    // Do not allow default sorting
    "order":[]
  });

  // Inform the user that their search terms will be ignored if
  // 'controversial', 'rising', or 'random rising' is selected in praw_sort
  $("#id_praw_sort").change(function () {
    let p = this.parentNode;
    let options = ["controversial", "rising", "random_rising"];
    if (options.includes(this.value)) {
      $('#terms-warning').show();
    } else {
      // Remove warning message if a viable option is selected
      $('#terms-warning').hide();
    }
  });

  // Ensure that only one option is selected for both the search options (url vs search terms)
  // and the time options (time_filter vs date range)
  $(".option-select").click(function () {
    if ($(this).attr("id") == "id_url_select") {
      $("#id_terms_select").prop("checked", false)
    } else if ($(this).attr("id") == "id_terms_select") {
      $("#id_url_select").prop("checked", false)
    } else if ($(this).attr("id") == "id_time_filter_select") {
      $("#id_date_range_select").prop("checked", false)
    } else if ($(this).attr("id") == "id_date_range_select") {
      $("#id_time_filter_select").prop("checked", false)
    }
  });

  // Add loading icon to search form submit button once clicked.
  $('#search_btn').click(function (event) {
    $('.loading-icon').show()
  });

  $("#remove-queries-form").submit(function (e) {
    e.preventDefault();
  })
 
  // Any .rm-btn element will need to be added to the ajax POST request
  // to properly update the history/favorites table
  $(".rm-btn").click(function (event) {
    let form = $(this).closest('form')[0];
    let action = form.action;
    let data = $(this).closest('form').serializeArray();

    let queryIds = [];
    let selectedRows = dTable.rows('.selected').data();
    $.each(selectedRows, function (i, item) {
      queryIds.push(item[8]);
    })

    // There must be at least one row selected.
    if (queryIds.length == 0) {
      alert("Please select at least one row.");
      return
    }

    // Add the clicked button and query ids to the serialized data.
    data.push({ name: this.name, value: this.value}, {name:'query_ids', value: JSON.stringify(queryIds)});

    // Create a POST ajax call. Send the query ids and serialized form data.
    $.ajax({
      type: "POST",
      url: action,
      data: data,
      success: function (response) {
        // Reload to display the updated table.
        location.reload();
      },
      error: function (response) {
        alert(response['error']);
      }
    });
  });

  // Send ajax request to download submission data
  $("#download-form").submit(function (event) {
    event.preventDefault();
    $('.loading-icon').show()

    // Gather the ids of the selected submissions
    let subIds = [];
    let selectedRows = dTable.rows('.selected').data();
    $.each(selectedRows, function (i, item) {
      subIds.push(item[8]);
    })

    // There must be at least one row selected.
    if (subIds.length == 0) {
      $('.loading-icon').hide()
      alert("Please select at least one row.");
      return
    }

    let data = $(this).serializeArray();
    data.push({ name: 'sub_ids', value: JSON.stringify(subIds) });

    // Create a POST ajax call. Send the submissions ids and serialized form data.
    $.ajax({
      type: "POST",
      url: this.action,
      data: data,
      success: function (response) {
        // Begin downloading the generated zip file.
        $('div.message-wrapper').show();
        location.replace(response['url'])
        $('.loading-icon').hide()
      },
      error: function (response) {
        $('.loading-icon').hide()

        // Get the error messages and append them to the appropriate form div.
        let err_str = response.responseJSON['error']
        let errors = JSON.parse(err_str)

        if ('submission_field_options' in errors && !$('#submission-fields p.errorlist').length) {
          let submissionFieldError = errors['submission_field_options'][0]['message']
          let inputDiv = $('#submission-fields')
          $("<p class='errorlist'>" + submissionFieldError + "</p>").appendTo(inputDiv);
        } else if (!('submission_field_options' in errors) && ($('#submission-fields p.errorlist').length)) {
          $('#submission-fields p.errorlist').remove()
        }

        if ('comment_field_options' in errors && !$('#comment-fields p.errorlist').length) {
          let commentFieldError = errors['comment_field_options'][0]['message']
          let inputDiv = $('#comment-fields')
          $("<p class='errorlist'>" + commentFieldError + "</p>").appendTo(inputDiv);
        } else if (!('comment_field_options' in errors) && ($('#comment-fields p.errorlist').length)) {
          $('#comment-fields p.errorlist').remove()
        }

        if ('comment_limit' in errors && !$('#comment-limit p.errorlist').length) {
          let commentLimitError = errors['comment_limit'][0]['message']
          let inputDiv = $('#comment-limit')
          $("<p class='errorlist'>" + commentLimitError + "</p>").appendTo(inputDiv);
        } else if (!('comment_limit' in errors) && ($('#comment-limit p.errorlist').length)) {
          $('#comment-limit p.errorlist').remove()
        }
      }
    });
  });
});
