$(document).ready(function () {
  let dTable = $("table.table").DataTable({
    columnDefs: [{
      // Allow selection of rows
      orderable: false,
      className: 'select-checkbox',
      targets: 0,
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
      if (!p.innerHTML.includes("<span")) {
        $("<span id='warning_message'>Search terms will be ignored for this option</span>").appendTo(p);
      }
    } else {
      // Remove warning message if a viable option is selected
      if (p.innerHTML.includes("<span")) {
        $("#warning_message").remove();
      }
    }
  });

  $('#remove-queries-form').submit(function (e) {
    e.preventDefault();
  })

  $(".rm-btn").click(function (event) {
    var form = $(this).closest('form')[0];
    let action = form.action
    let data = $(this).closest('form').serializeArray()

    let queryIds = []
    let selectedRows = dTable.rows('.selected').data();
    $.each(selectedRows, function (i, item) {
      queryIds.push(item[9])
    })

    // There must be at least one row selected.
    if (queryIds.length == 0) {
      alert("Please select at least one row.")
      return
    }

    // Add the clicked button and query ids to the serialized data.
    data.push({ name: this.name, value: this.value}, {name:'query_ids', value: JSON.stringify(queryIds)})

    // Create a POST ajax call. Send the submissions ids and serialized form data.
    $.ajax({
      type: "POST",
      url: action,
      data: data,
      success: function (data) {
        // Reload to display the updated table.
        location.reload();
      },
      error: function (data) {
        alert('error');
      }
    })
  });
});