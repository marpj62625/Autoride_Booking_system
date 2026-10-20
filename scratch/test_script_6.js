







    function viewLicenseImage(url) {



        var modal = document.getElementById('licensePreviewModal');



        var img = document.getElementById('licensePreviewImg');



        if (modal && img) {



            img.src = url;



            modal.style.display = 'flex';



        }



    }







