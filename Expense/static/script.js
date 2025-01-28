var id=0;
var amount=0;
var major;
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
let del_id = 0;

function verify_age(user_id, expense_id) {
    fetch(`/expense/verify_major`) // Use the correct endpoint
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json(); // Parse the JSON response
        })
        .then(data => {
            const ageMessage = document.getElementById("ageMessage");
            const deleteConfirmationSection = document.getElementById("deleteConfirmationSection");
            if (data.is_major) {
                del_id = expense_id; // Set global variable
                console.log(del_id)
                deleteConfirmationSection.style.display = "block"; // Show confirmation dialog
                
            } else {
                ageMessage.style.display = "block";
                ageMessage.style.animation = "none"; // Reset animation
                void ageMessage.offsetWidth; // Trigger reflow
                ageMessage.style.animation = "showHide 1.5s ease-in-out";
            }
        })
        .catch(error => console.error("Error:", error));
}

function deletion_f() {
    console.log("deletE_f",del_id)
    const form = document.getElementById('deleteConfirmationSection');
    form.action = `/expense/delete_expense/${del_id}`; // Dynamically set the form action
    form.submit()

    const deleteMessage = document.getElementById("deleteMessage");
    deleteMessage.style.display = "block";
    deleteMessage.style.animation = "none"; // Reset animation
    void deleteMessage.offsetWidth; // Trigger reflow
    deleteMessage.style.animation = "showHide 1.5s ease-in-out";
    
}


function close_delete(){
    document.getElementById('deleteConfirmationSection').style.display='none';
}



let lastDeletedExpense = null; // Store the last deleted expense ID

        function deleteExpense(expenseId, button) {
            // Perform the deletion via AJAX
            fetch(`/expense/delete_expense/${expenseId}`, {
              method: "POST",
            }).then((response) => {
              if (response.ok) {
                lastDeletedExpense = expenseId; // Store the deleted expense ID
                document.getElementById("undoSection").style.display = "block"; // Show the undo section
                button.closest("tr").style.display = "none"; // Hide the row

                // Set a timeout to automatically hide the undo option after a few seconds
                setTimeout(() => {
                  document.getElementById("undoSection").style.display = "none";
                  lastDeletedExpense = null; // Clear the last deleted expense
                }, 5000); // 5 seconds
              } else {
                console.error("Failed to delete expense");
              }
            });
        }

        function undoDeletion() {
            if (lastDeletedExpense) {
                // Logic to restore the deleted expense
                fetch(`/expense/restore_expense/${lastDeletedExpense}`, {
                  method: "POST",
                }).then((response) => {
                  if (response.ok) {
                    // Show the row again (you may need to fetch the data again)
                    const row = document.querySelector(
                      `tr[data-expense-id="${lastDeletedExpense}"]`
                    );
                    if (row) {
                      row.style.display = ""; // Show the row again
                    }

                    // Hide the undo section
                    document.getElementById("undoSection").style.display =
                      "none";
                    lastDeletedExpense = null; // Clear the last deleted expense
                  } else {
                    console.error("Failed to restore expense");
                  }
                });
            }
        }


        function show_rec_tab(){
            curr_state = document.getElementById('recc_exps').style.display
            if (curr_state=='block'){
             document.getElementById('recc_exps').style.display='none';
            }else{
             document.getElementById('recc_exps').style.display='block';
            }
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


