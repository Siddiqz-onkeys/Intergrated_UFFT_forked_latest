var id=0;
var amount=0;
var major;
window.onload = function() {
    let messageBox = document.getElementById("messageBox");
    if (messageBox) {
        setTimeout(() => {
            messageBox.classList.add("fade-out"); // Apply fade-out animation
        }, 3000); // Disappear after 3 seconds
    }
};

function fetch_back(){
    form=document.getElementById('user-selection');
    form.method="GET";
    form.submit();

}

function open_add_expense(){
    let elem = document.getElementById('add_expense');
    if (elem.style.display == 'block'){
        elem.style.display = 'none';
    } else {
        elem.style.display = 'block';

        // Hide other sections (replace 'other_id' with actual element IDs)
        document.getElementById('recc_exps').style.display = "none";
        document.getElementById('interval-selection').style.display = "none";
        document.getElementById('sorting_filtering').style.display = "none";
    }
}

function open_overview(){
    let elem = document.getElementById('interval-selection'); // Make sure this ID exists
    if (elem.style.display == 'block'){
        elem.style.display = 'none'
    } else {
        elem.style.display = 'block';

        document.getElementById('add_expense').style.display = "none";
        document.getElementById('recc_exps').style.display = "none";
        document.getElementById('sorting_filtering').style.display = "none";
    }
}

function open_filters(){
    let elem = document.getElementById('sorting_filtering'); // Make sure this ID exists
    if (elem.style.display == 'block'){
        elem.style.display = 'none';
    } else {
        elem.style.display = 'block';

        document.getElementById('add_expense').style.display = "none";
        document.getElementById('interval-selection').style.display = "none";
        document.getElementById('recc_exps').style.display = "none";
    }
}

function show_rec_tab(){
    let elem = document.getElementById('recc_exps');
    if (elem.style.display == 'block'){
        elem.style.display = 'none';
    } else {
        elem.style.display = 'block';

        document.getElementById('add_expense').style.display = "none";
        document.getElementById('interval-selection').style.display = "none";
        document.getElementById('sorting_filtering').style.display = "none";
    }
}


function showEditMenu(expense_id,expense_amount){
    document.getElementById('edit_menu').style.display='block';

    // expense id is globalized to share it to other functions as well

    id=expense_id;
    amount=expense_amount;
    document.getElementById("exp_id_edit").textContent=id;
    document.getElementById('return_amount').textContent=amount;
}

function edit_expense(){
    
    document.getElementById('edit_expense').style.display="block";
    document.getElementById('add_amount_form').style.display="none";
    const form = document.getElementById('edit_expense');
    form.action = `/expense/edit_expense/${id}`;
    
}

function add_amount(){
    document.getElementById('add_amount_form').style.display="block";
    document.getElementById('edit_expense').style.display="none";
    const form = document.getElementById('add_amount_form');
    form.action = `/expense/add_amount/${id}`;
    
}

function close_menu(){
    document.getElementById('add_amount_form').style.display='none';
    document.getElementById('edit_menu').style.display='none';
    
}

let originalOrder = []; // Stores the default order of rows.

function sortTable(columnIndex, header) {
    const table = document.querySelector("table tbody");
    const rows = Array.from(table.rows);

    // Save original order only once
    if (originalOrder.length === 0) {
        originalOrder = rows.map(row => row.cloneNode(true));
    }

    // Get current sort order from the header
    const currentOrder = header.getAttribute("data-sort-order");
    let newOrder;

    if (currentOrder === "none" || currentOrder === "desc") {
        // Sort in ascending order
        newOrder = rows.sort((rowA, rowB) => {
            const cellA = rowA.cells[columnIndex].innerText.trim();
            const cellB = rowB.cells[columnIndex].innerText.trim();
            return isNaN(cellA) ? cellA.localeCompare(cellB) : parseFloat(cellA) - parseFloat(cellB);
        });
        header.setAttribute("data-sort-order", "asc");
    } else if (currentOrder === "asc") {
        // Sort in descending order
        newOrder = rows.sort((rowA, rowB) => {
            const cellA = rowA.cells[columnIndex].innerText.trim();
            const cellB = rowB.cells[columnIndex].innerText.trim();
            return isNaN(cellA) ? cellB.localeCompare(cellA) : parseFloat(cellB) - parseFloat(cellA);
        });
        header.setAttribute("data-sort-order", "desc");
    } else {
        // Restore to default order
        newOrder = originalOrder;
        header.setAttribute("data-sort-order", "none");
    }

    // Clear the table and append the sorted rows
    table.innerHTML = "";
    newOrder.forEach(row => table.appendChild(row));

    // Reset other headers' sort order
    document.querySelectorAll("thead th").forEach(th => {
        if (th !== header) {
            th.setAttribute("data-sort-order", "none");
        }
    });
}

let del_id = null; // Variable to store the expense ID to be deleted

// Function to show the delete confirmation form
function delete_expense(expense_id) {
    del_id = expense_id; // Store the expense ID to be deleted
    document.getElementById("deleteConfirmationSection").style.display = "block"; // Show confirmation form
}

// Function to actually delete the expense
function deletion_f() {
    // Perform the deletion using the stored del_id
    const form =document.getElementById('deleteConfirmationSection')
    form.method="POST"
    form.action=`/expense/delete_expense/${del_id}`
    form.submit()
    // Close the confirmation form
    close_delete();
}

function rollbackDeletion() {
    fetch('/rollback_deletion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Success:', data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

// Function to close the delete confirmation form if the user clicks "Cancel"
function close_delete() {
    document.getElementById("deleteConfirmationSection").style.display = "none";
}



let rec_id_ = null;

function load_rec_to_exp(rec_id){
    rec_id_=rec_id
    document.getElementById('rec_exp_conf_div').style.display='block';
}

function add_rec_to_exp(){
    const form = document.getElementById('rec_exp_conf');
    if (rec_id_ !== null) {
        form.action = `/expense/add_rec_to_exp/${rec_id_}`;
    }
}

function overview(){
    const form=document.getElementById('interval-selection')
    form.submit()
    
}

let currentCardIndex = 0;

function showCard(index) {
    const flashcards = document.querySelectorAll('.flashcards');
    flashcards.forEach((card, i) => {
        card.classList.remove('active'); // Hide all cards
        if (i === index) {
            card.classList.add('active'); // Show the active card
        }
    });

    // Update arrow states
    updateArrowStates(index, flashcards.length);
}

function nextCard() {
    const flashcards = document.querySelectorAll('.flashcards');
    if (currentCardIndex < flashcards.length - 1) {
        currentCardIndex++;
        showCard(currentCardIndex);
    }
}

function prevCard() {
    if (currentCardIndex > 0) {
        currentCardIndex--;
        showCard(currentCardIndex);
    }
}

function updateArrowStates(index, totalCards) {
    const leftArrow = document.getElementById('left-arrow');
    const rightArrow = document.getElementById('right-arrow');

    // Disable left arrow if on the first card
    if (index === 0) {
        leftArrow.classList.add('disabled');
        leftArrow.style.pointerEvents = 'none';
    } else {
        leftArrow.classList.remove('disabled');
        leftArrow.style.pointerEvents = 'auto';
    }

    // Disable right arrow if on the last card
    if (index === totalCards - 1) {
        rightArrow.classList.add('disabled');
        rightArrow.style.pointerEvents = 'none';
    } else {
        rightArrow.classList.remove('disabled');
        rightArrow.style.pointerEvents = 'auto';
    }
}

// Ensure the first card is shown by default
document.addEventListener('DOMContentLoaded', () => {
    showCard(currentCardIndex);
});
