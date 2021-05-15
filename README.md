![](frontend/static/facialpay-logo.png)

# Summary
FacialPay is a face recognition based payment system for point of sale terminals. The goal is to eventually replace credit cards with biometrics (like face, retinal and/or fingerprint scan).

The `backend` folder contains all the backend code for face recognition and the implementation of the database system for payments. The `frontend` folder contains the code for the UI that allows POS payment.

# How?
Uses DNNs to detect faces at point of sale terminals before matching them with those stored in the banking systems database, letting the customer purchase a product from a verified seller almost instantaneously. Also allows for the splitting of a bill.

Explored using dlib as the deep learning framework for face detection and recognition, along with Flask for the web side of things. The front end uses AJAX to communicate with the back end server, and all requests are SSL-encrypted.
